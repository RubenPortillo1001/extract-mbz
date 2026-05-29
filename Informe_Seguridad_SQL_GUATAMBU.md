# Informe de Seguridad SQL Server — Servidor GUATAMBU
**Corte Suprema de Justicia del Paraguay — DCPI**

| Campo | Valor |
|-------|-------|
| Servidor | 172.30.8.30 — GUATAMBU |
| Host SQL | WIN-RMGLHEE42QQ |
| Fecha de auditoría | 07/04/2026 |
| Batch ID | `4CE85B97-47AF-4A6F-A68F-EA9455925DA9` |
| Bases de datos auditadas | 10 / 10 (100 %) |
| Unidad auditora | DCPI — División de Ciberseguridad y Protección de la Información |
| Marco de referencia | NIST SP 800-53 Rev. 5 |

---

## Tabla de contenido

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Configuración peligrosa del servidor](#2-configuración-peligrosa-del-servidor)
3. [Seguridad de logins del servidor](#3-seguridad-de-logins-del-servidor)
4. [Hallazgos por base de datos](#4-hallazgos-por-base-de-datos)
5. [Usuarios con acceso a múltiples bases de datos](#5-usuarios-con-acceso-a-múltiples-bases-de-datos)
6. [Mapeo NIST SP 800-53 Rev. 5](#6-mapeo-nist-sp-800-53-rev-5)
7. [Plan de remediación priorizado](#7-plan-de-remediación-priorizado)
8. [Scripts T-SQL de remediación](#8-scripts-t-sql-de-remediación)

---

## 1. Resumen ejecutivo

> **Estado general: CRÍTICO — Se requiere intervención inmediata.**
>
> El servidor GUATAMBU presenta vulnerabilidades que, en combinación, permiten a un atacante
> con acceso a cualquiera de las cuentas privilegiadas obtener **control total del sistema operativo
> Windows**, no solo de las bases de datos. La remediación de los cinco ítems de mayor prioridad
> puede completarse en una ventana de mantenimiento de 2 horas sin downtime prolongado.

### 1.1 Cuadro de hallazgos

| Nivel | Cantidad | Descripción resumida |
|-------|----------|----------------------|
| 🔴 CRÍTICO | **17** | Configuraciones OS-level, SA activa, db_owner masivo, sysadmin personal |
| 🟠 ALTO | **3** | CLR/remote access habilitados, usuario huérfano con permisos |
| 🟡 MEDIO | **9** | Logins sin expiración de contraseña, roles de backup sin justificar |
| 🔵 BAJO | **8** | Roles de lectura/grupos de aplicación a validar |
| **Total** | **37** | En 10 bases de datos + nivel de servidor |

### 1.2 Vulnerabilidades críticas resumidas

#### VUL-01 — xp_cmdshell habilitado `[CRÍTICO]`
`xp_cmdshell` está activo en la instancia. Este procedimiento permite ejecutar comandos arbitrarios
del sistema operativo Windows directamente desde T-SQL. Combinado con las cuentas db_owner y sysadmin
detectadas, cualquier usuario con esos roles puede ejecutar comandos como el usuario del servicio SQL Server.
**No existe ningún caso de uso legítimo en producción que justifique mantenerlo activo.**

**Remediación:** Desactivar inmediatamente con `sp_configure 'xp_cmdshell', 0`.
**Control NIST:** CM-6, CM-7

---

#### VUL-02 — Cuenta SA habilitada, score 100/100 `[CRÍTICO]`
La cuenta `sa` (System Administrator) está activa, con contraseña sin expiración desde el año **2003**
(8.400 días). Es el objetivo principal de ataques de fuerza bruta automatizados contra SQL Server.
Otorga privilegios irrestrictos sobre toda la instancia y no puede auditarse con granularidad.

**Remediación:** Cambiar contraseña a valor complejo y deshabilitar (`ALTER LOGIN [sa] DISABLE`).
**Control NIST:** AC-2, IA-5

---

#### VUL-03 — 5 cuentas con rol sysadmin `[CRÍTICO]`
Cuatro cuentas personales y una de dominio tienen el rol `sysadmin` en el servidor. Este rol otorga
control total sobre la instancia: acceso a todas las bases de datos, posibilidad de modificar
configuraciones del servidor, crear/eliminar logins y ejecutar cualquier operación.

| Login | Tipo | Acción |
|-------|------|--------|
| `sa` | SQL built-in | Deshabilitar (ver VUL-02) |
| `m_peralta` | SQL personal | Revocar sysadmin; también tiene db_owner en Consulres y JURDB |
| `s_villa` | SQL personal | Revocar sysadmin; también tiene db_owner en Consulres |
| `m_silvera` | SQL personal | Revocar sysadmin; también tiene db_owner en Consulres |
| `CSJ\appm1` | Windows dominio | Verificar si es cuenta de servicio; asignar permisos mínimos |

**Remediación:** `ALTER SERVER ROLE [sysadmin] DROP MEMBER [login];`
**Control NIST:** AC-3, AC-6

---

#### VUL-04 — 16 asignaciones de db_owner en 8 bases de datos de producción `[CRÍTICO]`
El rol `db_owner` otorga control total dentro de una base de datos: puede crear/eliminar objetos,
alterar permisos, hacer backup/restore y suplantar cualquier usuario. Ninguna cuenta operativa
ni de aplicación debería tenerlo.

| Base de datos | Usuarios con db_owner |
|---------------|----------------------|
| Consulres | s_insfran, j_sandoval, m_peralta, s_villa, g_rodriguez, m_silvera, **d_lopez** |
| JURDB | s_insfran, m_peralta |
| Lederes | rrijo, conexion_lederes, s_insfran |
| Sig_pub | usersigjur |
| Sig_pub_cov | usersigjur |
| Sig_pub_reg | usersigjur |
| secisys_csj | secisys |
| ContenedorDLL | D_Lopez *(huérfano)* |

> ⚠ **Alerta especial:** `d_lopez` fue creado el **2026-04-06**, un día antes de la auditoría,
> con db_owner sobre Consulres. Esto requiere investigación inmediata para descartar acceso no autorizado.

**Remediación:** `EXEC sp_droprolemember 'db_owner', '<usuario>';` y asignar rol mínimo.
**Control NIST:** AC-3, AC-6

---

#### VUL-05 — 2 usuarios huérfanos con permisos activos `[CRÍTICO/ALTO]`
Un usuario huérfano existe en la base de datos pero su login fue eliminado del servidor.
No puede autenticarse normalmente, pero puede ser re-vinculado por cualquier cuenta sysadmin
—incluyendo un atacante que tome control del servidor.

| Base de datos | Usuario huérfano | Rol en BD | Severidad |
|---------------|-----------------|-----------|-----------|
| ContenedorDLL | `D_Lopez` | db_owner | 🔴 CRÍTICO |
| Sig_pub_reg | `UserSigPub` | — | 🟠 ALTO |

**Remediación:** Revocar db_owner y ejecutar `DROP USER [<usuario>]` en cada BD.
**Control NIST:** AC-2, IA-4, PS-4

---

#### VUL-06 — CLR Enabled y Remote Access habilitados `[ALTO]`
- **CLR Enabled = 1:** Permite cargar ensamblados .NET externos en el proceso SQL Server.
  Un atacante con acceso suficiente puede subir código malicioso compilado para ejecutar con
  los privilegios del servicio.
- **Remote Access = 1:** Habilita conexiones RPC server-to-server (linked servers).
  Puede utilizarse para movimiento lateral dentro de la red interna de la CSJ.

**Remediación:** Desactivar ambas opciones con `sp_configure`.
**Control NIST:** CM-7, AC-17, SC-7

---

#### VUL-07 — 11 logins sin expiración de contraseña `[MEDIO]`
El 38 % de los logins SQL activos no tienen expiración de contraseña. Si una contraseña es
comprometida, permanece válida indefinidamente sin ningún mecanismo de detección.

Logins afectados: `user_resolucioncon`, `user_resolucioninterna`, `User_cba`, `UserIBERUS`,
`conexion_lederes`, `secisys`, `usersigjur`, `resolucion`, `cl_figueredo`, `WIN-RMGLHEE42QQ\Administrador`, `CSJ\appm1`.

**Remediación:** `ALTER LOGIN [login] WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;`
**Control NIST:** IA-5

---

#### VUL-08 — Cuentas deshabilitadas con roles activos en BD `[MEDIO]`
Los logins `rrijo` y `c_morinigo` están deshabilitados a nivel de servidor pero sus usuarios de BD
permanecen activos con roles asignados. La cuenta de `rrijo` tiene db_owner en Lederes.

**Remediación:** Eliminar o revocar roles de los usuarios de BD correspondientes.
**Control NIST:** AC-2, PS-4

---

#### VUL-09 — g_martinez con db_backupoperator en 9 bases de datos `[MEDIO]`
El usuario `g_martinez` tiene el rol `db_backupoperator` en las 9 bases de datos auditadas.
Este rol permite realizar y restaurar backups, lo que puede usarse para exfiltrar datos o
sobreescribir datos legítimos. Su presencia en todas las BDs requiere justificación documentada.

**Remediación:** Validar con DAI si esta cuenta necesita acceso de backup en todas las BDs.
Revocar en las BDs donde no corresponda.
**Control NIST:** AC-6

---

### 1.3 Tabla de remediación priorizada

| ID | Vulnerabilidad | Prioridad | Plazo | Responsable sugerido |
|----|---------------|-----------|-------|----------------------|
| VUL-01 | xp_cmdshell habilitado | **P1 — Inmediata** | 48 hs | DAI + DCPI |
| VUL-02 | Cuenta SA activa | **P1 — Inmediata** | 48 hs | DAI + DCPI |
| VUL-05 | Usuarios huérfanos con permisos | **P1 — Inmediata** | 48 hs | DAI |
| VUL-03 | sysadmin en cuentas personales | **P1 — Inmediata** | 48 hs | DAI |
| VUL-04 | db_owner masivo (16 asignaciones) | P2 — Corto plazo | 30 días | DAI + responsables de sistemas |
| VUL-06 | CLR / Remote Access | P2 — Corto plazo | 30 días | DAI |
| VUL-08 | Cuentas deshabilitadas con roles | P2 — Corto plazo | 30 días | DAI |
| VUL-07 | Logins sin expiración de contraseña | P2 — Corto plazo | 30 días | DAI |
| VUL-09 | g_martinez en 9 BDs | P3 — Mejora continua | 90 días | DAI |

---

## 2. Configuración peligrosa del servidor

Fuente: `ServerConfigAudit` (4 registros).

| Configuración | Valor actual | Valor recomendado | Riesgo | Control NIST |
|---------------|-------------|-------------------|--------|-------------|
| `xp_cmdshell` | **1 (ON)** | 0 (OFF) | 🔴 CRÍTICO | CM-6, CM-7 |
| `Cuenta SA` | **HABILITADA** | DESHABILITADA | 🔴 CRÍTICO | AC-2, IA-5 |
| `clr enabled` | **1 (ON)** | 0 (OFF) | 🟠 ALTO | CM-7, SI-3 |
| `remote access` | **1 (ON)** | 0 (OFF) | 🟠 ALTO | AC-17, SC-7 |

### Impacto de xp_cmdshell (el riesgo más grave)

`xp_cmdshell` permite ejecutar comandos del SO desde T-SQL. Con esta opción activa y múltiples
usuarios con `db_owner` o `sysadmin` detectados, el vector de ataque es directo:

```
Login SQL comprometido
  → escalada a db_owner (ya existe)
    → EXEC xp_cmdshell 'whoami'
      → control del OS Windows con privilegios del servicio SQL Server
        → acceso a archivos, red, Active Directory
```

### Impacto de CLR habilitado

Un atacante con permisos `CREATE ASSEMBLY` puede subir un ensamblado .NET que:
- Acceda al filesystem del servidor
- Realice conexiones de red salientes
- Eluda restricciones del motor SQL

### Impacto de Remote Access habilitado

Permite que este servidor SQL ejecute consultas en otros servidores SQL de la red CSJ
(linked servers via RPC). Si GUATAMBU es comprometido, se convierte en plataforma de
movimiento lateral hacia otras instancias.

---

## 3. Seguridad de logins del servidor

Fuente: `LoginSecurityAudit` (29 logins analizados).

### 3.1 Logins críticos y altos

| Login | Tipo | Score | Nivel | Problemas |
|-------|------|-------|-------|-----------|
| `sa` | SQL | 100 | 🔴 CRÍTICO | SA activa · Sin expiración · 8.400 días (2003) |
| `c_morinigo` | SQL | 85 | 🟠 ALTO | Sin política · Sin expiración · **DESHABILITADA** |
| `rrijo` | SQL | 85 | 🟠 ALTO | Sin política · Sin expiración · **DESHABILITADA** |

### 3.2 Logins con expiración de contraseña ausente (score ≥ 70)

| Login | Score | BD por defecto | Días de antigüedad |
|-------|-------|---------------|--------------------|
| `user_resolucioncon` | 70 | consulres | 1.924 |
| `user_resolucioninterna` | 70 | consulres | 1.924 |
| `User_cba` | 70 | JURDB | 1.924 |
| `UserIBERUS` | 70 | JURDB | 1.924 |
| `conexion_lederes` | 70 | lederes | 1.924 |
| `secisys` | 70 | secisys_csj | 1.924 |
| `usersigjur` | 70 | sig_pub | 1.924 |
| `resolucion` | 70 | Consulres | 762 |
| `cl_figueredo` | 70 | master | 183 |
| `WIN-RMGLHEE42QQ\Administrador` | 60 | master | 1.937 |
| `CSJ\appm1` | 60 | master | 397 |

> Los siete primeros logins tienen exactamente 1.924 días de antigüedad, lo que sugiere que fueron
> creados todos el mismo día (30/12/2020) como parte de la configuración inicial del servidor.
> Ninguno ha tenido rotación de contraseña en más de 5 años.

### 3.3 Sysadmin en el servidor (desde Hoja_General)

| Login | Tipo | Observación |
|-------|------|-------------|
| `sa` | SQL built-in | Ver VUL-02 |
| `m_peralta` | SQL personal | También db_owner en Consulres y JURDB |
| `s_villa` | SQL personal | También db_owner en Consulres |
| `m_silvera` | SQL personal | También db_owner en Consulres |
| `CSJ\appm1` | Windows dominio | Probable cuenta de servicio — verificar |

### 3.4 Cuentas deshabilitadas a nivel servidor con usuarios BD activos

| Login (deshabilitado) | Usuario en BD | Rol en BD | Riesgo |
|-----------------------|--------------|-----------|--------|
| `rrijo` | rrijo en Lederes | db_owner | 🔴 CRÍTICO |
| `c_morinigo` | (sin usuario BD detectado) | — | 🟡 MEDIO |
| `gs_martinez` | (sin usuario BD detectado) | — | 🟡 MEDIO |

---

## 4. Hallazgos por base de datos

Fuente: `AuditResults` (37 registros) y `AuditPerformanceLog` (10 BDs).

### 4.1 Resumen por base de datos

| Base de datos | Hallazgos | Críticos | Altos | Duración |
|---------------|-----------|----------|-------|----------|
| Consulres | 14 | 7 | 0 | 0 seg |
| JURDB | 6 | 2 | 0 | 0 seg |
| Lederes | 4 | 3 | 0 | 0 seg |
| Sig_pub_reg | 3 | 1 | 1 | 0 seg |
| secisys_csj | 2 | 1 | 0 | 1 seg |
| Sig_pub | 2 | 1 | 0 | 0 seg |
| Sig_pub_cov | 2 | 1 | 0 | 0 seg |
| ContenedorDLL | 1 | 1 | 0 | 0 seg |
| MOODLEDB | 1 | 0 | 0 | 0 seg |
| Uep_proyectos | 1 | 0 | 0 | 0 seg |

### 4.2 Consulres — 7 usuarios con db_owner

> Base de datos con mayor cantidad de hallazgos críticos del servidor (14 total).

| Usuario | Login | Rol | Creado | Score |
|---------|-------|-----|--------|-------|
| `s_insfran` | s_insfran | db_owner | 2020-12-30 | 95 |
| `j_sandoval` | j_sandoval | db_owner | 2021-08-09 | 95 |
| `m_peralta` | m_peralta | db_owner | 2021-08-11 | 95 |
| `s_villa` | s_villa | db_owner | 2022-05-09 | 95 |
| `g_rodriguez` | g_rodriguez | db_owner | 2024-05-31 | 95 |
| `m_silvera` | m_silvera | db_owner | 2024-09-03 | 95 |
| `d_lopez` | d_lopez | db_owner | **2026-04-06** | 95 |

> ⚠ **ALERTA:** `d_lopez` fue creado el 2026-04-06, exactamente **1 día antes** de la auditoría.
> Solicitar al equipo DAI quién autorizó y ejecutó la creación de este usuario. Revocar db_owner
> de forma inmediata mientras se investiga.

Hallazgos adicionales en Consulres (nivel BAJO):

| Usuario | Rol | Observación |
|---------|-----|-------------|
| `user_resolucioncon` | Grupo_Consulta | Validar necesidad |
| `user_resolucioninterna` | Grupo_ConsultaInterna | Validar necesidad |
| `b_rojas` | db_datareader + db_datawriter | Doble rol; validar si necesita escritura |
| `d_ibarra` | db_datareader | Validar necesidad |
| `r_olmedo` | grupo_BD | Validar necesidad |
| `resolucion` | grupo_BD | Validar necesidad |

### 4.3 JURDB — 2 db_owner + 4 roles menores

| Usuario | Rol | Nivel | Observación |
|---------|-----|-------|-------------|
| `s_insfran` | db_owner | 🔴 CRÍTICO | También db_owner en Consulres y Lederes |
| `m_peralta` | db_owner | 🔴 CRÍTICO | También db_owner en Consulres + sysadmin |
| `g_martinez` | db_backupoperator | 🟡 MEDIO | Presente en 9 BDs |
| `r_ruizdiaz` | db_datareader | 🔵 BAJO | Validar acceso |
| `User_cba` | Grupo_JUR | 🔵 BAJO | Validar necesidad |
| `UserIBERUS` | Grupo_WebService | 🔵 BAJO | Validar necesidad |

### 4.4 Lederes — 3 db_owner

| Usuario | Rol | Nivel | Observación |
|---------|-----|-------|-------------|
| `rrijo` | db_owner | 🔴 CRÍTICO | Login DESHABILITADO pero usuario BD activo |
| `conexion_lederes` | db_owner | 🔴 CRÍTICO | Cuenta de aplicación con privilegio excesivo |
| `s_insfran` | db_owner | 🔴 CRÍTICO | También db_owner en Consulres y JURDB |
| `g_martinez` | db_backupoperator | 🟡 MEDIO | Verificar necesidad |

### 4.5 Sig_pub / Sig_pub_cov / Sig_pub_reg — usersigjur como db_owner

> Una cuenta de aplicación **nunca** debe tener db_owner. Si la aplicación es comprometida
> (inyección SQL, credenciales expuestas), el atacante obtiene control total de las tres BDs.

| Base de datos | Usuario | Rol | Nivel |
|---------------|---------|-----|-------|
| Sig_pub | `usersigjur` | db_owner | 🔴 CRÍTICO |
| Sig_pub_cov | `usersigjur` | db_owner | 🔴 CRÍTICO |
| Sig_pub_reg | `usersigjur` | db_owner | 🔴 CRÍTICO |
| Sig_pub_reg | `UserSigPub` | — (huérfano) | 🟠 ALTO |
| Sig_pub | `g_martinez` | db_backupoperator | 🟡 MEDIO |
| Sig_pub_cov | `g_martinez` | db_backupoperator | 🟡 MEDIO |
| Sig_pub_reg | `g_martinez` | db_backupoperator | 🟡 MEDIO |

### 4.6 secisys_csj y ContenedorDLL

| Base de datos | Usuario | Rol | Nivel |
|---------------|---------|-----|-------|
| secisys_csj | `secisys` | db_owner | 🔴 CRÍTICO |
| secisys_csj | `g_martinez` | db_backupoperator | 🟡 MEDIO |
| ContenedorDLL | `D_Lopez` | db_owner + **HUÉRFANO** | 🔴 CRÍTICO |

### 4.7 MOODLEDB y Uep_proyectos

Ambas bases de datos presentan solo un hallazgo de nivel MEDIO: `g_martinez` con rol
`db_backupoperator`. No se detectaron db_owner ni permisos críticos en estas BDs.

---

## 5. Usuarios con acceso a múltiples bases de datos

> Un único vector de compromiso de estas cuentas afecta simultáneamente varias bases de datos.

| Usuario/Login | Bases de datos afectadas | Nivel máximo | Riesgo acumulado |
|--------------|--------------------------|-------------|-----------------|
| **s_insfran** | Consulres, JURDB, Lederes | db_owner en las 3 | 🔴 CRÍTICO MÁXIMO |
| **m_peralta** | Consulres, JURDB + sysadmin servidor | db_owner + sysadmin | 🔴 CRÍTICO MÁXIMO |
| **usersigjur** | Sig_pub, Sig_pub_cov, Sig_pub_reg | db_owner en las 3 | 🔴 CRÍTICO |
| **d_lopez** | Consulres (activo) + ContenedorDLL (huérfano) | db_owner | 🔴 CRÍTICO (creado 1 día antes) |
| **g_martinez** | Consulres, JURDB, Lederes, MOODLEDB, secisys_csj, Sig_pub, Sig_pub_cov, Sig_pub_reg, Uep_proyectos | db_backupoperator en 9 | 🟡 MEDIO — justificar |

---

## 6. Mapeo NIST SP 800-53 Rev. 5

### Estado de cumplimiento por control

| Control ID | Familia / Nombre | Estado | Hallazgos asociados |
|------------|-----------------|--------|---------------------|
| **AC-2** | Account Management | 🔴 INCUMPLIDO | SA activa · `rrijo`/`c_morinigo` deshabilitados con roles activos · `d_lopez` creado 1 día antes · 2 usuarios huérfanos |
| **AC-3** | Access Enforcement | 🔴 INCUMPLIDO | 16 asignaciones db_owner · 5 cuentas sysadmin |
| **AC-6** | Least Privilege | 🔴 INCUMPLIDO | Cuentas de aplicación con db_owner (`usersigjur`, `conexion_lederes`) · sysadmin en cuentas personales |
| **AC-17** | Remote Access | 🟠 PARCIAL | `remote access = 1` sin documentación ni justificación |
| **IA-4** | Identifier Management | 🔴 INCUMPLIDO | SA es identificador genérico compartido · usuarios huérfanos sin propietario activo |
| **IA-5** | Authenticator Management | 🔴 INCUMPLIDO | 11 logins sin expiración · 3 sin política de contraseñas · SA sin expiración desde 2003 |
| **CM-6** | Configuration Settings | 🔴 INCUMPLIDO | 4 de 4 configuraciones auditadas en estado peligroso |
| **CM-7** | Least Functionality | 🔴 INCUMPLIDO | `xp_cmdshell` y `CLR` habilitados sin justificación operativa |
| **SC-7** | Boundary Protection | 🟠 EN RIESGO | `remote access` habilita RPC server-to-server sin control de frontera |
| **AU-9** | Protection of Audit Information | 🟠 EN RIESGO | Con `xp_cmdshell` + sysadmin, los logs de auditoría pueden ser eliminados o alterados |
| **SI-3** | Malicious Code Protection | 🟠 EN RIESGO | `CLR enabled` permite cargar ensamblados .NET potencialmente maliciosos |
| **PS-4** | Personnel Termination | 🟡 PARCIAL | `rrijo` y `c_morinigo`: logins deshabilitados pero usuarios BD activos |

**Controles CRÍTICOS incumplidos:** AC-2 · AC-3 · AC-6 · IA-4 · IA-5 · CM-6 · CM-7 (7 controles)

---

## 7. Plan de remediación priorizado

### FASE 1 — Acción inmediata (P1): dentro de 48 horas

| # | Acción | Justificación | Impacto operativo |
|---|--------|--------------|-------------------|
| 1 | Deshabilitar `xp_cmdshell` | Mayor riesgo individual del servidor | Ninguno — no tiene uso legítimo en producción |
| 2 | Deshabilitar `CLR enabled` | Permite ejecución de código externo | Verificar con DAI si alguna BD usa CLR antes de deshabilitar |
| 3 | Deshabilitar `remote access` | Reduce movimiento lateral | Verificar si hay linked servers activos antes de deshabilitar |
| 4 | Cambiar contraseña y deshabilitar `sa` | Score 100, objetivo de ataques | Ninguno — usar cuenta sysadmin con nombre propio para administración |
| 5 | Investigar `d_lopez` (creado 2026-04-06) | Posible acceso no autorizado | Revocar db_owner mientras se investiga |
| 6 | Eliminar usuarios huérfanos | `D_Lopez` (db_owner) en ContenedorDLL, `UserSigPub` en Sig_pub_reg | Ninguno — usuarios que no pueden autenticarse normalmente |

### FASE 2 — Corto plazo (P2): dentro de 30 días

| # | Acción | Justificación |
|---|--------|--------------|
| 7 | Revocar sysadmin de m_peralta, s_villa, m_silvera, CSJ\appm1 | Principio de mínimo privilegio (AC-6) |
| 8 | Revocar db_owner de todas las BDs de producción | 16 asignaciones que exceden el mínimo necesario |
| 9 | Para cuentas de aplicación: asignar solo permisos que la app usa | `usersigjur`, `conexion_lederes`, `secisys` |
| 10 | Habilitar `CHECK_EXPIRATION` en 11 logins afectados | Prevenir uso indefinido de credenciales comprometidas |
| 11 | Eliminar o revocar roles de `rrijo` en Lederes | Login deshabilitado pero usuario BD activo con db_owner |

### FASE 3 — Mejora continua (P3): dentro de 90 días

| # | Acción |
|---|--------|
| 12 | Documentar y justificar acceso de `g_martinez` en 9 bases de datos |
| 13 | Implementar política formal de gestión de cuentas SQL (proceso de alta/baja) |
| 14 | Configurar SQL Server Audit para: LOGIN_FAILED, ADD_MEMBER_TO_DB_ROLE, ALTER_SERVER_CONFIGURATION |
| 15 | Extender esta auditoría a todas las instancias SQL Server de la red CSJ |
| 16 | Revisión semestral de accesos: validar que roles asignados siguen siendo necesarios |

---

## 8. Scripts T-SQL de remediación

> ⚠ **Instrucción de uso:** Ejecutar cada bloque en SSMS conectado a la instancia GUATAMBU
> como login con rol `sysadmin`. Hacer **backup del estado actual** antes de ejecutar cambios.
> Los bloques están organizados por fase y son independientes entre sí.

### FASE 1 — Scripts de acción inmediata

#### F1.1 — Deshabilitar xp_cmdshell, CLR y Remote Access

```sql
-- Verificar estado actual antes de modificar
SELECT name, value_in_use
FROM sys.configurations
WHERE name IN ('xp_cmdshell', 'clr enabled', 'remote access');

-- Deshabilitar las tres opciones
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;

EXEC sp_configure 'xp_cmdshell', 0;
RECONFIGURE;

EXEC sp_configure 'clr enabled', 0;
RECONFIGURE;

EXEC sp_configure 'remote access', 0;
RECONFIGURE;

EXEC sp_configure 'show advanced options', 0;
RECONFIGURE;

-- Verificar resultado
SELECT name, value_in_use
FROM sys.configurations
WHERE name IN ('xp_cmdshell', 'clr enabled', 'remote access');
```

#### F1.2 — Deshabilitar cuenta SA

```sql
-- PASO 1: Cambiar contraseña a valor complejo (reemplazar con valor real seguro)
ALTER LOGIN [sa] WITH PASSWORD = '<CONTRASEÑA_ALEATORIA_32_CHARS_AQUI>';

-- PASO 2: Deshabilitar la cuenta
ALTER LOGIN [sa] DISABLE;

-- Verificar
SELECT name, is_disabled FROM sys.server_principals WHERE name = 'sa';
```

#### F1.3 — Investigar y revocar d_lopez en Consulres

```sql
USE Consulres;

-- Ver información del usuario
SELECT dp.name, dp.create_date, dp.modify_date, dp.type_desc,
       sp.name AS login_name
FROM sys.database_principals dp
LEFT JOIN sys.server_principals sp ON dp.sid = sp.sid
WHERE dp.name = 'd_lopez';

-- Ver en qué roles está
SELECT r.name AS rol, m.name AS miembro
FROM sys.database_role_members rm
JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
JOIN sys.database_principals m ON rm.member_principal_id = m.principal_id
WHERE m.name = 'd_lopez';

-- Revocar db_owner (ejecutar luego de investigación)
-- EXEC sp_droprolemember 'db_owner', 'd_lopez';
```

#### F1.4 — Eliminar usuarios huérfanos

```sql
-- ContenedorDLL: primero revocar db_owner, luego eliminar usuario
USE ContenedorDLL;
EXEC sp_droprolemember 'db_owner', 'D_Lopez';
DROP USER [D_Lopez];

-- Sig_pub_reg: eliminar directamente (no tiene rol de DB, solo es huérfano)
USE Sig_pub_reg;
DROP USER [UserSigPub];
```

### FASE 2 — Scripts de corto plazo

#### F2.1 — Revocar sysadmin de cuentas personales

```sql
-- Verificar estado actual
SELECT sp.name, srm.role_principal_id
FROM sys.server_role_members srm
JOIN sys.server_principals sp ON srm.member_principal_id = sp.principal_id
JOIN sys.server_principals sr ON srm.role_principal_id = sr.principal_id
WHERE sr.name = 'sysadmin'
ORDER BY sp.name;

-- Revocar sysadmin (ejecutar uno por uno, confirmando con responsable)
ALTER SERVER ROLE [sysadmin] DROP MEMBER [m_peralta];
ALTER SERVER ROLE [sysadmin] DROP MEMBER [s_villa];
ALTER SERVER ROLE [sysadmin] DROP MEMBER [m_silvera];
-- CSJ\appm1: verificar si es cuenta de servicio antes de revocar
-- ALTER SERVER ROLE [sysadmin] DROP MEMBER [CSJ\appm1];
```

#### F2.2 — Revocar db_owner en bases de datos de producción

```sql
-- Plantilla: repetir para cada combinación BD / usuario
-- Reemplazar <BD> y <USUARIO> en cada ejecución

USE Consulres;
EXEC sp_droprolemember 'db_owner', 's_insfran';
EXEC sp_droprolemember 'db_owner', 'j_sandoval';
EXEC sp_droprolemember 'db_owner', 'm_peralta';
EXEC sp_droprolemember 'db_owner', 's_villa';
EXEC sp_droprolemember 'db_owner', 'g_rodriguez';
EXEC sp_droprolemember 'db_owner', 'm_silvera';
-- d_lopez: ver F1.3 primero

USE JURDB;
EXEC sp_droprolemember 'db_owner', 's_insfran';
EXEC sp_droprolemember 'db_owner', 'm_peralta';

USE Lederes;
EXEC sp_droprolemember 'db_owner', 'rrijo';
EXEC sp_droprolemember 'db_owner', 'conexion_lederes';
EXEC sp_droprolemember 'db_owner', 's_insfran';

USE secisys_csj;
EXEC sp_droprolemember 'db_owner', 'secisys';

USE Sig_pub;
EXEC sp_droprolemember 'db_owner', 'usersigjur';

USE Sig_pub_cov;
EXEC sp_droprolemember 'db_owner', 'usersigjur';

USE Sig_pub_reg;
EXEC sp_droprolemember 'db_owner', 'usersigjur';
```

#### F2.3 — Asignar roles mínimos para cuentas de aplicación

```sql
-- usersigjur (aplicación SIG público): asignar solo datareader+datawriter
-- Coordinar con el equipo de desarrollo qué permisos realmente necesita la app

USE Sig_pub;
EXEC sp_addrolemember 'db_datareader', 'usersigjur';
EXEC sp_addrolemember 'db_datawriter', 'usersigjur';

USE Sig_pub_cov;
EXEC sp_addrolemember 'db_datareader', 'usersigjur';
EXEC sp_addrolemember 'db_datawriter', 'usersigjur';

USE Sig_pub_reg;
EXEC sp_addrolemember 'db_datareader', 'usersigjur';
EXEC sp_addrolemember 'db_datawriter', 'usersigjur';
```

#### F2.4 — Habilitar expiración de contraseñas

```sql
-- Verificar logins sin expiración activos
SELECT name, is_expiration_checked, is_policy_checked, is_disabled
FROM sys.sql_logins
WHERE is_expiration_checked = 0
  AND is_disabled = 0
ORDER BY name;

-- Habilitar expiración en logins afectados
-- NOTA: Luego de ejecutar, el login deberá cambiar su contraseña al próximo acceso
ALTER LOGIN [user_resolucioncon]    WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;
ALTER LOGIN [user_resolucioninterna] WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;
ALTER LOGIN [User_cba]              WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;
ALTER LOGIN [UserIBERUS]            WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;
ALTER LOGIN [conexion_lederes]      WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;
ALTER LOGIN [secisys]               WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;
ALTER LOGIN [usersigjur]            WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;
ALTER LOGIN [resolucion]            WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;
ALTER LOGIN [cl_figueredo]          WITH CHECK_EXPIRATION = ON, CHECK_POLICY = ON;
```

### Consulta de verificación post-remediación

```sql
-- Ejecutar en SecurityAudit después de remediar para confirmar el estado

USE SecurityAudit;

-- Ver si quedan configs peligrosas activas
SELECT ConfigName, CurrentValue, RecommendedValue, RiskLevel
FROM dbo.ServerConfigAudit
WHERE CurrentValue <> RecommendedValue
ORDER BY RiskLevel DESC;

-- Ver si quedan db_owner en BDs de producción
SELECT DatabaseName, PrincipalName, RoleName, RiskLevel
FROM dbo.AuditResults
WHERE RoleName = 'db_owner'
ORDER BY DatabaseName;

-- Ver si quedan logins sin expiración activos
SELECT LoginName, Issues
FROM dbo.LoginSecurityAudit
WHERE Issues LIKE '%SIN_EXPIRACIÓN%'
  AND Issues NOT LIKE '%DESHABILITADA%'
ORDER BY RiskScore DESC;
```

---

*Informe generado por DCPI — División de Ciberseguridad y Protección de la Información*
*Corte Suprema de Justicia del Paraguay*
*Batch ID: `4CE85B97-47AF-4A6F-A68F-EA9455925DA9` — Auditoría: 07/04/2026*
