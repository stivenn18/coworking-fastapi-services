# ==============================================================================
# Script de Pruebas Rápidas - Taller 3 (AWS RDS + MongoDB Atlas)
# ==============================================================================

$py = "C:\Users\stive\AppData\Local\Python\pythoncore-3.14-64\python.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "     SUITE DE PRUEBAS: BASES DE DATOS EN LA NUBE          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Probar AWS RDS PostgreSQL
Write-Host "`n[1] Consultando ordenes en AWS RDS PostgreSQL..." -ForegroundColor Yellow
& $py -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:CoworkingSecure2026!@coworking-postgres-rds.cgpscm88mvbm.us-east-1.rds.amazonaws.com:5432/coworking_db'); cur = conn.cursor(); cur.execute('SELECT id, space_name, user_email, hours, total_price, status, created_at FROM orders;'); rows = cur.fetchall(); print(f'Total de ordenes en AWS RDS: {len(rows)}'); [print(f'  - Orden #{r[0]}: {r[1]} | Usuario: {r[2]} | Total: ${r[4]} | Estado: {r[5]}') for r in rows]"

# 2. Probar MongoDB Atlas (Analytics)
Write-Host "`n[2] Consultando eventos y agregaciones en MongoDB Atlas..." -ForegroundColor Yellow
& $py -c "from pymongo import MongoClient; c = MongoClient('mongodb+srv://zukabarcenas_db_user:miCePLAc8643pLYh@cluster0.bcov6bc.mongodb.net/coworking_analytics?retryWrites=true&w=majority'); db = c.coworking_analytics; print(f'Total de eventos en Atlas: {db.events.count_documents({})}'); pipeline = [{'$group': {'_id': '$space_name', 'total_ordenes': {'$sum': 1}, 'ingresos': {'$sum': '$total_price'}}}]; print('Metricas Agregadas:'); [print(f'  - Espacio: {doc[\"_id\"]} | Ordenes: {doc[\"total_ordenes\"]} | Ingresos: ${doc[\"ingresos\"]}') for doc in db.events.aggregate(pipeline)]"

# 3. Insertar una nueva orden de prueba en ambas nubes
Write-Host "`n[3] Insertando una nueva orden de prueba sincronizada..." -ForegroundColor Yellow
& $py -c "import psycopg2, datetime; conn = psycopg2.connect('postgresql://postgres:CoworkingSecure2026!@coworking-postgres-rds.cgpscm88mvbm.us-east-1.rds.amazonaws.com:5432/coworking_db'); cur = conn.cursor(); cur.execute('INSERT INTO orders (space_id, space_name, user_email, hours, price_per_hour, total_price, status, created_at) VALUES (3, %s, %s, 2, 50.0, 100.0, %s, NOW()) RETURNING id;', ('Meeting Room Alpha', 'profesor@universidad.edu', 'CONFIRMED')); new_id = cur.fetchone()[0]; conn.commit(); print(f'  ✓ Nueva orden creada en AWS RDS con ID #{new_id}'); from pymongo import MongoClient; c = MongoClient('mongodb+srv://zukabarcenas_db_user:miCePLAc8643pLYh@cluster0.bcov6bc.mongodb.net/coworking_analytics?retryWrites=true&w=majority'); doc_id = c.coworking_analytics.events.insert_one({'event_type': 'ORDER_CREATED', 'order_id': new_id, 'space_id': 3, 'space_name': 'Meeting Room Alpha', 'user_email': 'profesor@universidad.edu', 'hours': 2, 'total_price': 100.0, 'timestamp': datetime.datetime.utcnow().isoformat()}).inserted_id; print(f'  ✓ Evento registrado en MongoDB Atlas Doc ID: {doc_id}')"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "     ¡PRUEBAS COMPLETADAS EXITOSAMENTE!                   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
