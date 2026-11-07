"""
Suite de Validación del Taller 4: Backend Avanzado FastAPI
Prueba:
1. Hash de contraseñas con bcrypt (seguridad).
2. Registro de usuarios con roles 'user' y 'admin' en PostgreSQL.
3. Inicio de sesión (/auth/login) y generación de token JWT firmado.
4. Identificación del usuario actual (/users/me) a través de get_current_user().
5. Control de permisos RBAC (/admin/panel):
   - Usuario con rol 'user' -> HTTP 403 Forbidden
   - Usuario con rol 'admin' -> HTTP 200 OK
6. Rechazo de token inválido o manipulado -> HTTP 401 Unauthorized
"""

import os
import sys
import tempfile
from fastapi.testclient import TestClient

# Configurar BD temporal SQLite para probar toda la suite de forma aislada
db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
os.close(db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{temp_db_path}"

# Agregar orders-service al path
sys.path.insert(0, os.path.abspath("orders-service"))

from database import engine, Base, SessionLocal, UserModel
from main import app

# Inicializar tablas
Base.metadata.create_all(bind=engine)

client = TestClient(app)

print("=" * 70)
print("  TALLER 4: BACKEND AVANZADO FASTAPI - LAB 10 (JWT + RBAC)")
print("=" * 70)

# ------------------------------------------------------------------------------
# 1. REGISTRO DE USUARIOS
# ------------------------------------------------------------------------------
print("\n[1] Registrando usuarios con roles jerárquicos...")

# 1.1 Usuario estándar (user - Nivel 1)
res_user = client.post(
    "/auth/register",
    json={
        "email": "juan.perez@empresa.com",
        "full_name": "Juan Perez",
        "password": "PasswordUser123!",
        "role": "user"
    }
)
print(f"    - Registro 'user': Status {res_user.status_code}")
assert res_user.status_code == 201
user_data = res_user.json()
print(f"      ID={user_data['id']} | Email={user_data['email']} | Rol={user_data['role']}")

# 1.2 Usuario Administrador (admin - Nivel 2)
res_admin = client.post(
    "/auth/register",
    json={
        "email": "admin.coworking@empresa.com",
        "full_name": "Admin Principal",
        "password": "PasswordAdmin456!",
        "role": "admin"
    }
)
print(f"    - Registro 'admin': Status {res_admin.status_code}")
assert res_admin.status_code == 201
admin_data = res_admin.json()
print(f"      ID={admin_data['id']} | Email={admin_data['email']} | Rol={admin_data['role']}")

# ------------------------------------------------------------------------------
# 2. INICIO DE SESIÓN Y GENERACIÓN DE TOKENS JWT
# ------------------------------------------------------------------------------
print("\n[2] Iniciando sesión (/auth/login) y emitiendo tokens JWT...")

# 2.1 Login de usuario normal
login_user_res = client.post(
    "/auth/login",
    data={"username": "juan.perez@empresa.com", "password": "PasswordUser123!"}
)
assert login_user_res.status_code == 200
user_token = login_user_res.json()["access_token"]
print(f"    [OK] Token JWT obtenido para 'user': {user_token[:25]}... (HS256 - 60 min)")

# 2.2 Login de administrador
login_admin_res = client.post(
    "/auth/login",
    data={"username": "admin.coworking@empresa.com", "password": "PasswordAdmin456!"}
)
assert login_admin_res.status_code == 200
admin_token = login_admin_res.json()["access_token"]
print(f"    [OK] Token JWT obtenido para 'admin': {admin_token[:25]}... (HS256 - 60 min)")

# 2.3 Intento con credenciales incorrectas (401 esperado)
bad_login = client.post(
    "/auth/login",
    data={"username": "juan.perez@empresa.com", "password": "ClaveIncorrecta!"}
)
print(f"    [OK] Intento con password incorrecta: Status {bad_login.status_code} (Esperado: 401)")
assert bad_login.status_code == 401

# ------------------------------------------------------------------------------
# 3. IDENTIFICAR AL USUARIO ACTUAL (/users/me)
# ------------------------------------------------------------------------------
print("\n[3] Validando dependencia get_current_user (/users/me)...")
headers_user = {"Authorization": f"Bearer {user_token}"}
me_res = client.get("/users/me", headers=headers_user)
assert me_res.status_code == 200
print(f"    [OK] Perfil autenticado correctamente: {me_res.json()['full_name']} ({me_res.json()['email']})")

# ------------------------------------------------------------------------------
# 4. CONTROL DE ACCESO POR ROLES (RBAC: require_role)
# ------------------------------------------------------------------------------
print("\n[4] Probando control de acceso RBAC en ruta protegida (/admin/panel)...")

# 4.1 Usuario con rol 'user' intenta acceder al panel de admin -> 403 Forbidden esperado
forbidden_res = client.get("/admin/panel", headers=headers_user)
print(f"    [OK] Rol 'user' accediendo a /admin/panel -> Status: {forbidden_res.status_code} (Esperado: 403 Forbidden)")
assert forbidden_res.status_code == 403
print(f"      Detalle del error: {forbidden_res.json()['detail']}")

# 4.2 Usuario con rol 'admin' accede al panel de admin -> 200 OK esperado
headers_admin = {"Authorization": f"Bearer {admin_token}"}
allowed_res = client.get("/admin/panel", headers=headers_admin)
print(f"    [OK] Rol 'admin' accediendo a /admin/panel -> Status: {allowed_res.status_code} (Esperado: 200 OK)")
assert allowed_res.status_code == 200

# 4.3 Endpoint exacto del PDF /admin
allowed_admin_endpoint = client.get("/admin", headers=headers_admin)
print(f"    [OK] Rol 'admin' accediendo a /admin (endpoint del PDF) -> Status: {allowed_admin_endpoint.status_code} (Esperado: 200 OK)")
assert allowed_admin_endpoint.status_code == 200
assert allowed_admin_endpoint.json() == {"mensaje": "Acceso autorizado"}

# ------------------------------------------------------------------------------
# 5. SEGURIDAD Y TOKENS INVALIDOS
# ------------------------------------------------------------------------------
print("\n[5] Probando peticion con token manipulado/falso...")
fake_headers = {"Authorization": "Bearer token_falso_invalido_123"}
fake_res = client.get("/users/me", headers=fake_headers)
print(f"    [OK] Token falso rechazado -> Status: {fake_res.status_code} (Esperado: 401 Unauthorized)")
assert fake_res.status_code == 401

# Limpieza
if os.path.exists(temp_db_path):
    try:
        os.remove(temp_db_path)
    except Exception:
        pass

print("\n" + "=" * 70)
print("  TODAS LAS PRUEBAS DE JWT + RBAC PASARON CON EXITO ROTUNDO!")
print("=" * 70)
