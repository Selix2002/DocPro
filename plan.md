# Plan de Auditoría — DocPro

> Auditoría estática realizada sobre la rama `master` (commit `373b7e7`, v1.0.2).
> El proyecto es una aplicación de escritorio Windows construida con **PySide6** (no Flet, como sugería el brief inicial) + SQLAlchemy/Alembic sobre SQLite, empaquetada con PyInstaller e instalada con Inno Setup.
> Toda la información aquí es de **solo lectura**; no se modificó ningún archivo fuente.

---

## Resumen ejecutivo

- **Seguridad de credenciales frágil**: la llave Fernet en `~/.docpro/secret.key` se escribe con permisos por defecto (0644 en POSIX; ACL heredada en Windows) y las funciones de descifrado (`encryption_service.py:27,37`) no capturan `InvalidToken`/`JSONDecodeError`, por lo que un archivo corrupto o una llave rotada cuelgan la app en el arranque de cualquier flujo que toque Gmail o Groq.
- **Cálculos monetarios en `float`**: cotizaciones y totales usan `round(neto * 0.19, 2)` y `int(round(...))` en varias vistas (`items_table.py:20,211,231,233`, `totals_bar.py:8`), lo que produce pérdidas de centavos y desalineaciones entre UI, BD y PDF. En Chile el IVA es 19% exacto y cualquier discrepancia se ve en la factura.
- **Servicios monolíticos (>1000 LOC)**: `services/quote_service.py` (1187 líneas) y `services/report_service.py` (1006 líneas) mezclan UI, autosave, IO de PDF, envío por Gmail y persistencia; hacen imposible test unitario y concentran deuda técnica.
- **Errores silenciados de manera sistemática**: existen ~31 bloques `except Exception:` sin logging (usan `print(...)` a stdout o `lambda _: None`), lo que oculta fallos reales del usuario en producción (`docpro.log` sólo captura errores explícitos en `main.py`).
- **Riesgos de build/CI**: el workflow descarga GTK3 desde una URL hardcodeada de enero de 2022 sin verificar checksum, y el `.spec` de PyInstaller depende de rutas absolutas de Windows para localizar las DLL de GTK3. La reproducibilidad y la integridad del artefacto distribuido dependen de recursos externos frágiles.

---

## Hallazgos priorizados

### 🔴 Críticos (bloquean uso o comprometen datos)

- **Descifrado sin manejo de errores en `EncryptionService`** — `frontend/src/docpro_frontend/services/encryption_service.py:27,37`
    - `load_groq_key()` y `load_gmail_token()` invocan `self._fernet.decrypt(...)` sin `try/except`. Si la llave Fernet fue regenerada (por reinstalar), si los `.enc` están truncados, o si `gmail_token.enc` no es JSON válido tras descifrar, se lanza `cryptography.fernet.InvalidToken` o `json.JSONDecodeError` no controlado.
    - **Impacto**: cualquier flujo que llame `is_connected()`, `get_credentials()` o `AI Improve` propagará la excepción al hilo principal y probablemente cierre la app o rompa el envío de correo. No hay UX de recuperación.
    - **Propuesta**: envolver ambas cargas en `try/except (InvalidToken, ValueError, OSError)` que registre el error con `logging.exception(...)`, elimine el archivo corrupto y devuelva `None`, forzando reconexión.

- **Descarga de GTK3 sin verificación en el pipeline de release** — `.github/workflows/build.yml:32-34`
    - Se descarga `gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe` desde GitHub Releases de terceros con `Invoke-WebRequest` sin `-Verify`, sin checksum SHA-256 y sin pinning inmutable.
    - **Impacto**: si el asset desaparece o es sustituido, la próxima release no se puede compilar. Peor: si el repositorio de terceros es comprometido, el instalador distribuido bundlearía DLL maliciosas firmadas por el propio pipeline (supply-chain).
    - **Propuesta**: hospedar el instalador en un asset del propio repo (o Actions cache/artefacto interno), comparar SHA-256 antes de ejecutar, y fijar la versión de GTK3 en un archivo `dependencies.lock`.

- **Race condition en autoguardado + creación duplicada** `[a verificar]` — `frontend/src/docpro_frontend/services/quote_service.py` (ver `_do_autosave`, `_on_created`, `_pending_back/_pending_finalize`, aprox. líneas 140-220)
    - El timer de autoguardado (debounce 800 ms) puede dispararse mientras aún no ha vuelto la respuesta del `Worker` que crea el documento. Si el usuario altera campos entre el disparo y la respuesta, se envía un segundo `create` con `doc_id=None`.
    - **Impacto**: cotizaciones fantasma duplicadas en la BD, cada una capturando parte de los cambios, más una posible sobrescritura del `doc_id` interno.
    - **Propuesta**: introducir un `_saving_lock` (bandera o `QMutex`) que bloquee lanzar nuevos autoguardados mientras haya uno en vuelo; si llegan cambios durante ese lapso, marcar `_dirty=True` y disparar un guardado inmediatamente tras el callback.

- **`preview_locked` sin reset defensivo bloquea la vista previa** — `frontend/src/docpro_frontend/services/quote_service.py:494-506` y equivalente en `report_service.py:427-438`
    - Cuando `_render_pdf_preview` falla o el `Worker` muere sin emitir `result`/`error`, `_preview_locked` queda `True` para siempre y toda futura vista previa (Ctrl+S) queda inhibida hasta reiniciar.
    - **Impacto**: usuario cree que el sistema ignora la orden; no hay indicador visual del bloqueo.
    - **Propuesta**: liberar `_preview_locked` en un `finally` (o timer de rescate ~15 s) y mostrar un toast si el render falló.

### 🟠 Altos (afectan estabilidad o UX significativamente)

- **Cálculos monetarios en `float`** — `frontend/src/docpro_frontend/quote/views/items_table.py:20,211,231,233`, `frontend/src/docpro_frontend/quote/views/totals_bar.py:8`
    - `iva = round(neto * 0.19, 2)`, `subtotal = round(qty * price, 2)` y `_fmt_clp(int(round(value)))` acumulan errores de coma flotante y truncan a entero antes de formatear.
    - **Impacto**: descuadres de centavos entre línea, subtotal, IVA y total, especialmente en cotizaciones con muchos ítems o precios de tres decimales; también divergencia con lo que el backend guarde/renderice en PDF.
    - **Propuesta**: migrar el manejo de dinero a `decimal.Decimal` con `ROUND_HALF_UP` (Chile) y una utilidad central `format_clp(Decimal)` que redondee a la unidad correcta según la moneda.

- **Rutas GTK3 hardcodeadas en el `.spec`** — `docpro.spec:69-73`
    - `_GTK_CANDIDATES` sólo cubre tres rutas Windows conocidas. Si el runner CI o el equipo de desarrollo instala GTK3 en otro lugar, el bloque `else` emite un warning pero deja la lista de DLL vacía y sigue compilando.
    - **Impacto**: el instalador se genera sin las DLL de WeasyPrint y la app crashea al primer PDF en el equipo del usuario final.
    - **Propuesta**: convertir el warning en `raise SystemExit` (para forzar detectar el fallo en CI) o al menos añadir un `assert _gtk_binaries` antes de `Analysis`.

- **Fuga de PDFs temporales** — `frontend/src/docpro_frontend/services/report_service.py:842-900` (y patrón equivalente en `quote_service.py`)
    - Cada preview/exportación crea un archivo en `tempfile.gettempdir()/docpro/preview_*.pdf` sin borrarlo. Ctrl+S múltiples veces = decenas de PDFs residuales por sesión.
    - **Impacto**: consumo de disco no acotado; posible exposición de datos sensibles (las temp files no llevan permisos restrictivos).
    - **Propuesta**: usar `tempfile.NamedTemporaryFile(delete=True)` o llevar un registro `self._tmp_paths` que se limpie al cerrar la ventana / cambiar de documento.

- **`main.py` raíz es un stub sin uso** — `main.py:1-6`
    - Contiene `print("Hello from docpro!")` y no arranca la app real. Existe además `frontend/src/docpro_frontend/main.py` que es la entrada real (ver `docpro.spec:256`).
    - **Impacto**: confunde a desarrolladores nuevos y a herramientas externas; un `python main.py` desde la raíz no hace lo que aparenta.
    - **Propuesta**: eliminar el archivo o convertirlo en un shim que delegue a `docpro_frontend.main:main`.

- **Cascadas destructivas en el modelo de datos** — `backend/src/docpro_backend/schema/documents/documents.py:31-42` `[a verificar en el archivo exacto]`
    - Las relaciones usan `cascade="all, delete-orphan"`, por lo que borrar un `Document` elimina Quote/Report/Version/SendLog sin auditoría ni soft-delete.
    - **Impacto**: cualquier bug en la ruta de borrado (por ejemplo, un click en la papelera sin confirmación) puede destruir historial fiscalmente relevante.
    - **Propuesta**: introducir soft-delete (`deleted_at`) o al menos exigir confirmación explícita y guardar snapshot en `document_versions` antes de borrar.

- **Errores silenciados en el motor de autoguardado y de red** — `services/quote_service.py:228,305,380,401,455,511,690`, `services/report_service.py:206,283,387,443,622`, `dashboard_widget.py:185,205,284`
    - Usan `print(...)` a `stdout`, que en el bundle frozen sin consola no se ve por ningún lado; en modo debug se pierde entre ruido. Complementariamente, hay `worker.signals.error.connect(lambda _: None)` en `quote_service.py:62,262,288` y `report_service.py:77,240,266` que descartan errores.
    - **Impacto**: cuando un usuario reporta "no se guardó" no hay traza en `%APPDATA%/DocPro/docpro.log`.
    - **Propuesta**: reemplazar todos los `print(...)` por `logger = logging.getLogger(__name__)` + `logger.exception(...)`; los `lambda _: None` deben al menos enviar el error al toast global o al log.

### 🟡 Medios (deuda técnica, mejoras importantes)

- **Sin validación de correo ni teléfono al crear/editar cliente** — `frontend/src/docpro_frontend/clients/views/client_form_dialog.py:93-94,130-134`
    - El formulario acepta cualquier string. Consecuencia: envío de correo falla más adelante con "recipient inválido" sin apuntar al cliente creador.
    - **Propuesta**: aplicar `QRegularExpressionValidator` o validación explícita en `_validate()` antes de emitir `saved`.

- **Feedback visual del formulario de cliente acumula estilos** — `frontend/src/docpro_frontend/clients/views/client_form_dialog.py:145-163`
    - Concatena `border: 1px solid #EF4444;` al `styleSheet()` en cada intento de guardado. Corregir un campo no elimina el borde rojo del otro.
    - **Propuesta**: usar `setProperty("invalid", True)` + `style().unpolish/polish` para alternar clase, o mantener dos hojas de estilo (`_STYLE_OK`, `_STYLE_ERR`) y reasignar entera.

- **Botón "Guardar" del diálogo de cliente no se deshabilita mientras se ejecuta el worker** — `frontend/src/docpro_frontend/clients/views/client_form_dialog.py:166-167`
    - `saved.emit(...)` + `accept()` cierran el diálogo antes de que el `Worker` responda, y en el intermedio se puede reabrir/duplicar el envío. Además, si el usuario hace doble click rápido pueden crearse dos clientes.
    - **Propuesta**: deshabilitar el botón y esperar `_on_client_mutated` / `_on_client_mutation_error` antes de cerrar; mostrar spinner.

- **`_fmt_clp` truncando el detalle** — `frontend/src/docpro_frontend/quote/views/items_table.py:20`, `frontend/src/docpro_frontend/quote/views/totals_bar.py:8`
    - `int(round(value))` pierde cualquier decimal significativo (aunque en CLP normalmente sean 0, no lo es en USD/EUR si se internacionaliza).
    - **Propuesta**: formatear con `Decimal.quantize(Decimal("0.01"))` y locale.

- **`_get_credentials_path()` mezcla convenciones POSIX y Windows** — `frontend/src/docpro_frontend/services/gmail_service.py:20-30,45-49`
    - En sistemas sin `APPDATA`, recae a `Path.home()`. Pero el mensaje de error hardcodea `{appdata}\\credentials.json`.
    - **Propuesta**: unificar rutas con `Path` y usar `str(appdata)` sin backslash literal.

- **`OAUTHLIB_RELAX_TOKEN_SCOPE` seteado globalmente** — `frontend/src/docpro_frontend/services/gmail_service.py:41`
    - Se muta `os.environ` una vez y se deja así para siempre en el proceso.
    - **Propuesta**: restringir el `env` únicamente durante `flow.run_local_server(...)` (por ejemplo con `contextlib.contextmanager`).

- **`credentials.refresh(Request())` sin timeout** — `frontend/src/docpro_frontend/services/gmail_service.py:101`
    - Un DNS caído deja el hilo colgado indefinidamente; el `Worker` no se puede cancelar.
    - **Propuesta**: pasar un `Request(timeout=10)` propio y capturar `TransportError`.

- **`Content-Disposition` construido con `.format` y sin escape** — `frontend/src/docpro_frontend/services/gmail_service.py:143-146`
    - `f'attachment; filename="{path.name}"'` no escapa comillas ni CRLF. Aunque `path.name` viene de `Path`, es controlable por el usuario a través del nombre del PDF exportado.
    - **Propuesta**: usar `email.utils.encode_rfc2231` o `email.message.EmailMessage.add_attachment(..., filename=...)`, que hace el encoding correcto.

- **Validación de tamaño total de adjuntos con race** — `frontend/src/docpro_frontend/mail/views/email_composer_dialog.py:157-162`
    - Si un adjunto es borrado entre el chequeo y el envío, `p.stat().st_size` lanza `OSError` que se silencia y el envío puede exceder 25 MB.
    - **Propuesta**: guardar la lista de rutas verificadas y usarlas inmutables al construir el MIME; abortar con mensaje claro si el archivo desapareció.

- **Fuente única de verdad para `show_iva` frágil** — `frontend/src/docpro_frontend/quote/views/quote_form.py:138`
    - `getattr(rm, "show_iva", True)` funciona salvo si el backend envía `show_iva=None` explícito (por ejemplo cotización antigua migrada). `bool(None)` = `False`.
    - **Propuesta**: `getattr(rm, "show_iva", True) or False if rm.show_iva is None else rm.show_iva` o normalizar en el DTO.

- **Redibujo excesivo al escribir cantidades/precios** — `frontend/src/docpro_frontend/quote/views/items_table.py:159-172`
    - Cada `textChanged` recalcula totales aunque el usuario esté a mitad de tecla.
    - **Propuesta**: debouncear con un `QTimer.singleShot(150, self._recalc_totals)` compartido.

- **Migración con `PRAGMA writable_schema = ON`** — `backend/alembic/versions/d3e4f5a6b7c8_add_aprobado_rechazado_status.py`
    - Manipula `sqlite_master` para saltarse cascadas. Es un hack válido, pero peligroso si otra migración altera la misma tabla sin repetir el patrón.
    - **Propuesta**: documentar en `docs/migrations.md` la razón y añadir un `pragma integrity_check` post migración (ya lo hace, mantener).

- **SQL crudo con f-string en migración FTS** — `backend/alembic/versions/e5f6a7b8c9d0_fix_fts_client_name_index.py:49-69`
    - El contenido es literal, pero establece un mal patrón: interpolación directa dentro de `op.execute(f"""...""")`.
    - **Propuesta**: reemplazar por `sa.text(...)` con `bindparams` para todas las migraciones futuras.

- **Autosave sin límite en `SessionLocal` si la excepción ocurre antes del `try`** — `services/quote_service.py` (workers ~740-1173), `services/report_service.py` (workers ~684-988)
    - Patrón común: `session = SessionLocal(); try: ...` – si la construcción del session falla el `try` no cubre el `close()`.
    - **Propuesta**: usar `with SessionLocal() as session:` (soportado en SQLAlchemy 2.x).

- **Chocolatey y `setup-python` con versiones flotantes** — `.github/workflows/build.yml:19-23,45-46`
    - `python-version: '3.13'` y `choco install innosetup --yes` no fijan `patch` ni versión del compilador.
    - **Propuesta**: pinear (`python-version: '3.13.1'`, `choco install innosetup --version 6.4.3`).

- **CI sin cache de dependencias** — `.github/workflows/build.yml:27-28`
    - `uv sync --all-packages` reinstala todo en cada release. Ralentiza (10+ min) el build.
    - **Propuesta**: añadir `actions/cache` sobre `~/.cache/uv` claveado por `uv.lock`.

- **Ausencia total de tests automatizados**
    - Los archivos `backend/test_pdf_quote.py` y `backend/test_pdf_report.py` no son tests `pytest` sino scripts manuales (no hay `test_*` funciones ni asserts). No hay carpeta `tests/` ni CI que ejecute tests.
    - **Propuesta**: añadir suite mínima con `pytest` cubriendo (a) cálculo de totales/IVA, (b) render PDF con datos ficticios, (c) migraciones idempotentes en base temporal.

### 🟢 Bajos (nice-to-have, pulido)

- **`backend/src/docpro_backend/__init__.py`** — expone `def main(): print("Hello from docpro_backend!")` como script principal. Basura de plantilla; eliminar o convertir en `--help`.
- **Iniciales de contactos frágiles** — `frontend/src/docpro_frontend/clients/widgets/client_card.py:133-139` y `clients/widgets/clients_row.py:123-129`: `parts[0][:2]` asume >=1 palabra; el fallback `"??"` funciona pero la lógica es enredada.
- **`network.py:6`** — `timeout=2` insuficiente en redes móviles lentas; considerar 5 s y hacerlo configurable.
- **`_fetch_clients` de 107 líneas** — `frontend/src/docpro_frontend/services/clients_service.py:33-139`: mezcla stats, paginación y sort; extraer helpers.
- **Diálogo de error UX** — `dashboard_widget.py:262-271` reemplaza el color del botón usando `.replace(...)` sobre el CSS; frágil ante cualquier cambio de paleta.
- **`_active` set en `worker.py:9-34`** — no es formalmente thread-safe (bien mitigado por GIL pero conviene un `Lock` para futuro sin GIL).
- **Búsqueda de clientes sin límite superior de longitud** — `services/clients_service.py:86-91,101-106`: un input muy grande genera queries costosas en SQLite.
- **`_query_id` de búsqueda sin protección** — `services/search_service.py:87-88`: mismo comentario que `worker.py`.
- **`_credentials_src` bundleado desde `~/.docpro/`** — `docpro.spec:59-62`: el `.spec` incluye `credentials.json` del desarrollador si existe; peligro de subir el instalador con las creds del dev por error. Añadir `raise` explícito o `assert False` si se detecta.
- **`.gitignore`** — recientemente añade `/docpro-site` y `/web`; funcionan, pero el archivo carece de `Newline at end of file` (los diffs generan la queja `\ No newline at end of file`).

---

## Análisis por módulo

### `clients/`

- **Estructura**: `views/client_form_dialog.py`, `views/clients_widget.py`, y widgets (`client_card`, `clients_row`, `clients_grid`, `clients_table`, `filter_bar`, `pagination_bar`, `stats_bar`). El flujo CRUD sigue el patrón `Widget → señal → Worker → SessionLocal`.
- **Bugs relevantes**: falta de validación de email/teléfono (`client_form_dialog.py:93-134`); acumulación de estilos rojos (`145-163`); botón "Guardar" sin bloqueo (`166-167`).
- **Riesgo memoria** `[a verificar]`: `clients_grid.py:49-51` y `clients_table.py:109-111` llaman `deleteLater()` en widgets antiguos pero no desconectan sus señales; en navegación intensa entre páginas pueden quedar señales sin destinatario limpio.
- **Servicio**: `clients_service.py:180,201,229` — `except Exception: session.rollback(); raise` sin logging.

### `quote/`

- **Archivos principales**: `quote_widget.py` (73 LOC, orquestador), `quote_form.py` (367 LOC), `items_table.py` (243 LOC), `client_section.py`, `preview_panel.py`, `totals_bar.py`.
- **Servicio monolítico**: `services/quote_service.py` (1187 LOC) — 15+ funciones worker, 20+ métodos en la clase. Recomendado partir en `quote_service_ui.py` (UI), `quote_workers.py` (funciones puras que usan `SessionLocal`) y `quote_pdf.py` (render/preview).
- **IVA opcional (feature v1.0.2)**: `quote_form.py:138`, migración `f1a2b3c4d5e6_add_show_iva_to_quotes.py`. Riesgo: valor `None` legacy interpretado como `False`.
- **Autoguardado**: race condition documentada en críticos.
- **Cálculos**: `float` en toda la cadena — ver hallazgos altos.

### `report/`

- **Estructura**: `report_widget.py`, `report_form.py`, `report_header.py`, `meta_row.py`, `preview_panel.py`, `sections_list.py`, `section_block.py`, `subsection_card.py`, `trabajo_section.py`.
- **Servicio**: `services/report_service.py` (1006 LOC) con los mismos vicios del `quote_service`.
- **Bug crítico específico**: fuga de temp files (`842-900`).
- **JSON parsing silencioso**: `report_form.py:256-269` — `except (ValueError, KeyError): pass` descarta secciones "Trabajo efectuado" corruptas sin avisar.
- **Firma opcional**: `report_service.py:856,873,894` — si `get_firma()` devuelve `imagen=None`, el render del backend puede fallar sin validación.

### `mail/`

- **Un solo archivo**: `mail/views/email_composer_dialog.py` (290 LOC).
- **Bugs relevantes**: race en validación de tamaño (`157-162`); construcción de MIME `Content-Disposition` con f-string; sin whitelist de tipos MIME.
- **Depende de `services/gmail_service.py`** para el envío real.

### `services/`

- **`quote_service.py` / `report_service.py`**: monolitos con misma clase de problemas (errores silenciados, `float`, fuga de temp files, worker leaks potenciales).
- **`encryption_service.py`**: cifrado Fernet con clave en `~/.docpro/secret.key`; ausencia de captura de errores en descifrado (crítico).
- **`gmail_service.py`**: OAuth flow con parsing de `id_token` sin validar (`58-63`), `refresh` sin timeout (`101`), `OAUTHLIB_RELAX_TOKEN_SCOPE` global (`41`).
- **`groq_service.py`**: sin retry ni backoff; `except Exception:` en `_call_once` (línea 36) sin log.
- **`worker.py`**: patrón correcto (`setAutoDelete(False)` + set global). Sólo un `set` global no-thread-safe (menor, GIL protege).
- **`network.py`**: `is_online` bloqueante 2 s; si se llama en UI thread congela.
- **`settings_service.py` / `history_service.py` / `search_service.py` / `dashboard_service.py`**: no revisados a fondo; se recomienda pasada dedicada.
- **`backup_service.py`**: no revisado; identificar si toca la BD directamente para asegurar coherencia con las migraciones.

### `widgets/`

- **`suggestion_bubble.py`**: modificado recientemente; revisar diff (hallazgos no específicos detectados).
- **`ai_improve_button.py`**: correcto; carga la API key vía `EncryptionService`; vulnerable si el descifrado tira excepción (ver crítico).
- **`fallback_toast.py`, `success_toast.py`**: pequeños, sin hallazgos.

### Backend

- **Estructura Clean-ish**: `db/`, `schema/`, `repositories/`, `dtos/`, `services/`, `templates/`. Bien separado.
- **Motor SQLAlchemy en módulo top-level**: `backend/src/docpro_backend/db/engine.py:22-25` crea el engine al importar el módulo; `check_same_thread=False` permite compartir conexión entre hilos, adecuado para Qt pero exige que cada worker use su propio `SessionLocal()` (lo cumple).
- **Riesgo**: `engine.py:16` usa `os.environ["APPDATA"]` sin fallback (KeyError si falta la variable).
- **Migraciones**: 7 revisiones. Riesgos indicados en hallazgos (writable_schema hack, f-string SQL).
- **Repositorio FTS**: `repositories/documents/documents.py:39-48` — `text("... MATCH :query")` correctamente parametrizado; la búsqueda del usuario NO se sanitiza en longitud (ver bajos).
- **Cascadas**: descritas en altos; auditar todos los `cascade=` de `schema/`.
- **`repair_data.py`, `seeder.py`**: scripts manuales con `except Exception: pass` (líneas 300, 489). Documentar que son de mantenimiento y NO deben ejecutarse contra BD productiva.

### Build / empaquetado

- **`docpro.spec`**: hallazgos altos (rutas GTK3 hardcodeadas; ausencia de `raise` cuando no se encuentran). Positivo: excluye correctamente `hupper`, `tkinter`, `pandas`, etc. para reducir tamaño. Genera dos ejecutables (`DocPro`, `DocPro-debug`) desde el mismo build (bien).
- **`docpro.iss`**: instalador solo copia `dist\DocPro\DocPro.exe` + `_internal\*`. Si en un futuro release PyInstaller cambia el layout (por ejemplo `_internal` deja de generarse por switch a onefile), la instalación quedará incompleta sin error hasta el runtime.
- **Icono opcional**: `docpro.spec:296` — usa el icono solo si existe; correcto.

### CI/CD

- **`.github/workflows/build.yml`**: dispara sólo con tags `v*`. Sin job de test/lint, sin `matrix` de Python, sin cache, sin firma digital del `.exe`.
- Riesgos ya priorizados: URL GTK3 sin checksum (crítico), versiones flotantes (medio), sin cache (medio).

---

## Recomendaciones de proceso

### Testing
- Introducir `pytest` con al menos 3 suites: `test_finance.py` (cálculo de IVA/subtotales con `Decimal`), `test_migrations.py` (aplicar todas las migraciones sobre `sqlite:///:memory:`), `test_pdf_smoke.py` (renderizar un PDF minimal de cotización y reporte y verificar bytes > 0). Ejecutarlos en el workflow antes del PyInstaller.
- Migrar `backend/test_pdf_quote.py` y `backend/test_pdf_report.py` a `tests/` con `pytest.fixture` y asserts.
- Añadir `pytest-qt` para probar diálogos críticos (cliente, cotización), en particular la doble-emisión de "Guardar".

### Logging y observabilidad
- Sustituir sistemáticamente `print(...)` por `logging.getLogger(__name__)` en `services/`, `dashboard_widget.py` y `main.py`.
- Configurar `logging.handlers.RotatingFileHandler` (5 MB × 5 archivos) en `_setup_logging()` de `frontend/src/docpro_frontend/main.py:57-73` para evitar que `docpro.log` crezca sin límite.
- Enviar los errores del `Worker` a un dispatcher global que muestre `FallbackToast` cuando estén en modo release.

### Documentación
- Añadir `CONTRIBUTING.md` con: cómo generar el build (`uv run pyinstaller docpro.spec`), cómo firmar el `.exe`, cómo colocar `credentials.json` en dev y en producción, cómo rotar la clave Fernet.
- Documentar en `docs/architecture.md` el flujo Widget→Signal→Worker→Session y las convenciones de logging.
- Escribir un runbook para "el instalador falló": comprobar `%APPDATA%/DocPro/docpro.log`, comprobar GTK3.

### Gestión de dependencias
- Añadir `dependabot.yml` o `renovate.json` para monitorear parches de `cryptography`, `weasyprint`, `sqlalchemy`, `pdfplumber`, `pymupdf`, `google-api-python-client`.
- Añadir un job `uv pip audit` en CI para detectar CVEs conocidos.
- Consolidar dependencias en `pyproject.toml` raíz (hoy sólo `hupper` y `pyinstaller` como dev, todo lo demás vive en `backend/pyproject.toml`, lo que es inusual para una app frontend).

---

## Plan de ejecución sugerido

### Sprint 1 (bloqueadores y seguridad) — foco crítico
1. **[S]** Rodear las llamadas a `Fernet.decrypt` de `try/except` con logging y recuperación (`encryption_service.py`).
2. **[S]** Añadir timeout y logging al `refresh(Request())` de Gmail y sanitizar `Content-Disposition`.
3. **[M]** Introducir SHA-256 y hosting propio para el instalador GTK3 en `build.yml`; convertir el warning del `.spec` en error.
4. **[M]** Implementar cleanup de PDFs temporales (report + quote).
5. **[S]** Liberar `preview_locked` en `finally` + toast de error.
6. **[S]** Añadir mutex al autoguardado de `quote_service.py`.
7. **[S]** Eliminar/renombrar `main.py` raíz.
**Dependencias**: 1 y 2 pueden ir en paralelo con 3-4-5-6.

### Sprint 2 (finanzas y datos) — foco correctitud
1. **[L]** Migrar cálculos monetarios a `Decimal` en cotizaciones (`items_table.py`, `totals_bar.py`, `quote_service.py`, DTOs/repositorios que reciban totales) y en reportes.
2. **[M]** Introducir soft-delete o confirmación adicional en el modelo `Document` + tests de migración.
3. **[M]** Reemplazar todos los `print(...)` de servicios por `logger.exception`; agregar `RotatingFileHandler`.
4. **[S]** Validar `show_iva` para cotizaciones legacy.
**Dependencias**: 1 requiere Sprint 1 completo para no mezclar refactor con parches de seguridad.

### Sprint 3 (mantenibilidad) — foco arquitectura
1. **[L]** Refactorizar `quote_service.py` y `report_service.py` en 3-4 módulos (UI, workers, PDF, envío).
2. **[M]** Aislar `SessionLocal()` con `with` context manager en todos los workers.
3. **[M]** Añadir `pytest` + primeros 3 suites de test (finanzas, migraciones, PDF smoke) y correrlos en CI.
4. **[S]** Fijar versiones (`python-version`, `choco install ... --version`) y añadir `actions/cache` para `uv`.
5. **[S]** Deshabilitar botón "Guardar" en `client_form_dialog` mientras el worker corre.
6. **[S]** Sustituir la manipulación de `styleSheet` por `setProperty("invalid", True)`.

### Sprint 4 (pulido) — bajos y hardening
1. **[S]** Validar email/teléfono en `client_form_dialog` (regex central compartida con `new_client_dialog`).
2. **[S]** Añadir dependabot/renovate + `uv pip audit` en CI.
3. **[S]** Añadir `assert _gtk_binaries` y salida limpia si falta GTK3 al compilar en local.
4. **[S]** Extraer validación RUT a un módulo compartido (hoy duplicada en varios diálogos).
5. **[S]** Ampliar timeout de `network.is_online` y hacer llamada asíncrona.

---

## Preguntas abiertas

1. ¿La versión distribuida al usuario final necesita coincidir contable/legalmente con lo que se muestra en el PDF? Si es sí, la migración de `float → Decimal` sube a **Crítico**.
2. ¿Hay compromiso con clientes existentes que ya tienen cotizaciones legacy con `show_iva IS NULL`? Confirmar antes de tratar `None` como `True` para no cambiar retroactivamente el importe visible.
3. ¿Existe un plan de firma digital del `.exe` (Authenticode)? Sin firma, SmartScreen bloqueará el instalador en muchas máquinas — impacta la percepción de calidad.
4. ¿La aplicación soporta o soportará multi-usuario en el mismo Windows? Si es sí, la llave Fernet compartida y la BD SQLite en `%APPDATA%\DocPro` deben ser rediseñadas.
5. ¿Los scripts `backend/repair_data.py` y `backend/seeder.py` se ejecutan alguna vez contra la BD del cliente (por soporte)? Si es así, deben tener sus propias garantías (backups automáticos, dry-run, logging).
6. ¿Existe backup automático de la BD del usuario? El `backup_service.py` no fue auditado a fondo; conviene confirmar frecuencia y ubicación.
7. ¿Está previsto migrar de SQLite a un motor con concurrencia real (PostgreSQL) si crece el uso? Muchas decisiones actuales (session global, `check_same_thread=False`) son SQLite-específicas.
