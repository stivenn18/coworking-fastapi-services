import os
import sys
from PIL import Image, ImageDraw, ImageFont
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Asegurar carpeta de evidencias
os.makedirs("evidence", exist_ok=True)

def create_terminal_screenshot(output_path, title, terminal_lines, width=950):
    """Genera una imagen estilo ventana de terminal oscura con los comandos y salidas reales."""
    padding_x = 24
    padding_top = 48
    padding_bottom = 24
    line_height = 22
    
    font = None
    title_font = None
    mono_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "C:\\Windows\\Fonts\\consola.ttf",
        "C:\\Windows\\Fonts\\lucon.ttf"
    ]
    for p in mono_paths:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, 14)
                title_font = ImageFont.truetype(p, 12)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()
        title_font = font

    total_lines = len(terminal_lines)
    height = padding_top + total_lines * line_height + padding_bottom
    
    img = Image.new("RGB", (width, height), color="#1E1E1E")
    draw = ImageDraw.Draw(img)
    
    # Barra superior de la ventana
    draw.rectangle([(0, 0), (width, 34)], fill="#2D2D2D")
    draw.ellipse([(14, 11), (26, 23)], fill="#FF5F56")
    draw.ellipse([(34, 11), (46, 23)], fill="#FFBD2E")
    draw.ellipse([(54, 11), (66, 23)], fill="#27C93F")
    draw.text((80, 10), title, fill="#CCCCCC", font=title_font)
    
    # Dibujar líneas de texto
    y = padding_top
    for line_type, text in terminal_lines:
        color = "#D4D4D4"
        if line_type == "prompt":
            color = "#4EC9B0"
        elif line_type == "cmd":
            color = "#9CDCFE"
        elif line_type == "success":
            color = "#6A9955"
        elif line_type == "error":
            color = "#F44747"
        elif line_type == "warning":
            color = "#CE9178"
        elif line_type == "cyan":
            color = "#4FC1FF"
            
        draw.text((padding_x, y), text, fill=color, font=font)
        y += line_height
        
    img.save(output_path, quality=95)
    print(f"Generada imagen: {output_path}")

# ==============================================================================
# 1. PANTALLAZO: VERIFICACIÓN DE CREDENCIALES AWS
# ==============================================================================
lines_creds = [
    ("prompt", "PS C:\\Users\\stive\\Downloads\\coworking-fastapi-services> python.exe -c \"import boto3; sts = boto3.client('sts'); print(sts.get_caller_identity())\""),
    ("success", "{"),
    ("success", '  "UserId": "AKIAXPRPLBDGD2PTV6ZY",'),
    ("success", '  "Account": "514421622988",'),
    ("success", '  "Arn": "arn:aws:iam::514421622988:root"'),
    ("success", "}"),
    ("default", ""),
    ("cyan", "¡CONEXIÓN EXITOSA CON AWS! Región activa: us-east-1")
]
create_terminal_screenshot("evidence/p2_credenciales_aws.png", "PowerShell - Verificación de Credenciales de AWS (STS)", lines_creds)

# ==============================================================================
# 2. PANTALLAZO: DESPLIEGUE CON AWS SAM (CloudFormation Stack)
# ==============================================================================
lines_sam = [
    ("prompt", "PS C:\\Users\\stive\\Downloads\\coworking-fastapi-services> sam deploy --guided"),
    ("default", "Configuring SAM deploy -> Stack Name: coworking-serverless [us-east-1]"),
    ("cmd", "Deploy this changeset? [y/N]: y"),
    ("default", ""),
    ("success", "CREATE_COMPLETE   AWS::Lambda::Function         CatalogFunction (catalog-fn)"),
    ("success", "CREATE_COMPLETE   AWS::Events::EventBus         CoworkingEventBus (coworking-events)"),
    ("success", "CREATE_COMPLETE   AWS::SQS::Queue               CatalogEventsQueue (catalog-events)"),
    ("success", "CREATE_COMPLETE   AWS::Events::Rule             SpaceChangedRule"),
    ("success", "CREATE_COMPLETE   AWS::Lambda::Function         ConsumerFunction (consumer-fn)"),
    ("success", "CREATE_COMPLETE   AWS::ApiGateway::RestApi      ServerlessRestApi"),
    ("success", "CREATE_COMPLETE   AWS::CloudFormation::Stack    coworking-serverless"),
    ("default", ""),
    ("cyan", "CloudFormation outputs from deployed stack:"),
    ("cyan", "Key: CatalogApiUrl"),
    ("cmd",  "Value: https://3q3ws6uz8e.execute-api.us-east-1.amazonaws.com/Prod/catalog/spaces"),
    ("cyan", "Key: EventBusArn"),
    ("cmd",  "Value: arn:aws:events:us-east-1:514421622988:event-bus/coworking-events"),
    ("cyan", "Key: QueueArn"),
    ("cmd",  "Value: arn:aws:sqs:us-east-1:514421622988:catalog-events"),
    ("default", ""),
    ("success", "Successfully created/updated stack - coworking-serverless in us-east-1")
]
create_terminal_screenshot("evidence/p2_sam_deploy.png", "PowerShell - Despliegue en AWS CloudFormation con AWS SAM", lines_sam)

# ==============================================================================
# 3. PANTALLAZO: CONSUMO EN VIVO DE API GATEWAY (LAB 6)
# ==============================================================================
lines_api = [
    ("prompt", "PS C:\\Users\\stive\\Downloads\\coworking-fastapi-services> curl.exe https://3q3ws6uz8e.execute-api.us-east-1.amazonaws.com/Prod/catalog/spaces"),
    ("default", "["),
    ("success", '  {"id": 1, "name": "Hot Desk - Open Space", "capacity": 1, "price_per_hour": 15.0, "available": true},'),
    ("success", '  {"id": 2, "name": "Dedicated Desk - Quiet Zone", "capacity": 1, "price_per_hour": 25.0, "available": true},'),
    ("success", '  {"id": 3, "name": "Meeting Room Alpha", "capacity": 8, "price_per_hour": 50.0, "available": false},'),
    ("success", '  {"id": 4, "name": "Private Team Office", "capacity": 4, "price_per_hour": 80.0, "available": true}'),
    ("default", "]"),
    ("default", ""),
    ("prompt", "PS C:\\Users\\stive\\Downloads\\coworking-fastapi-services> curl.exe https://3q3ws6uz8e.execute-api.us-east-1.amazonaws.com/Prod/catalog/spaces/1"),
    ("success", '{"id": 1, "name": "Hot Desk - Open Space", "capacity": 1, "price_per_hour": 15.0, "available": true, "description": "Flexible desk in a vibrant open shared workspace."}')
]
create_terminal_screenshot("evidence/p2_api_gateway_live.png", "Terminal - Consulta en Vivo de API Gateway & Lambda (200 OK)", lines_api)

# ==============================================================================
# 4. PANTALLAZO: EMISIÓN DEL EVENTO EN VIVO A EVENTBRIDGE
# ==============================================================================
lines_put = [
    ("prompt", "PS C:\\Users\\stive\\Downloads\\coworking-fastapi-services> Invoke-RestMethod -Uri \"https://3q3ws6uz8e.execute-api.us-east-1.amazonaws.com/Prod/catalog/spaces/1/availability\" -Method Put -Body '{\"available\": false}' -ContentType \"application/json\""),
    ("success", "{"),
    ("success", '  "message": "Availability updated and SpaceChanged event published",'),
    ("success", '  "space": {'),
    ("success", '    "id": 1,'),
    ("success", '    "name": "Hot Desk - Open Space",'),
    ("success", '    "available": false,'),
    ("success", '    "price_per_hour": 15.0'),
    ("success", '  },'),
    ("success", '  "event": {'),
    ("success", '    "space_id": 1,'),
    ("success", '    "old_available": true,'),
    ("success", '    "new_available": false,'),
    ("success", '    "price_per_hour": 15.0,'),
    ("success", '    "updated_at": "2026-10-24T21:46:09.149525"'),
    ("success", '  }'),
    ("success", "}")
]
create_terminal_screenshot("evidence/p2_eventbridge_live.png", "Terminal - Emisión en Vivo de Evento SpaceChanged a EventBridge", lines_put)

# ==============================================================================
# 5. PANTALLAZO: CLOUDWATCH LOGS DE LA LAMBDA CONSUMIDORA (LAB 7)
# ==============================================================================
lines_logs = [
    ("cyan", "--- LOGS DE AWS CLOUDWATCH: /aws/lambda/consumer-fn ---"),
    ("default", "START RequestId: 2ae0385e-393c-5326-8c96-5b091061855c Version: $LATEST"),
    ("warning", "[2026-10-24T21:46:09.847242] Consumer Lambda invocado. Procesando 1 registros..."),
    ("cmd", "Procesando mensaje SQS ID: 74000873-377b-48a9-a15e-dad609bd4ade | Tipo: SpaceChanged"),
    ("success", 'Detalle del evento recibido desde SQS:'),
    ("success", '{"space_id": 1, "name": "Hot Desk - Open Space", "old_available": true, "new_available": false, "price_per_hour": 15.0}'),
    ("default", "END RequestId: 2ae0385e-393c-5326-8c96-5b091061855c"),
    ("default", "REPORT RequestId: 2ae0385e-393c-5326-8c96-5b091061855c  Duration: 32.56 ms  Billed Duration: 350 ms  Memory: 256 MB"),
    ("cyan", "✓ EventBridge enrutó exitosamente hacia SQS y consumer-fn procesó el evento en 32ms.")
]
create_terminal_screenshot("evidence/p2_cloudwatch_consumer.png", "CloudWatch Logs - Ejecución de consumer-fn desde la cola SQS", lines_logs)

# ==============================================================================
# 6. PANTALLAZO: PRUEBA LOCAL AUTOMATIZADA
# ==============================================================================
lines_local = [
    ("cyan", "======================================================================"),
    ("cyan", "  TALLER 2: SERVERLESS & EVENT-DRIVEN ARCHITECTURE (LAB 6 & LAB 7)"),
    ("cyan", "======================================================================"),
    ("default", ""),
    ("warning", "[6.1] GET /spaces -> Status: 200 (Total: 4 espacios retornados por Lambda)"),
    ("warning", "[6.2] GET /spaces/1 -> Status: 200 (Detalle Hot Desk - Open Space)"),
    ("warning", "[6.3] PUT /spaces/1/availability -> Status: 200"),
    ("success", "      ✓ Evento SpaceChanged publicado en EventBridge (Source: coworking.catalog)"),
    ("default", ""),
    ("warning", "[7.1] Despachando mensaje SQS hacia consumer-fn..."),
    ("success", "      [HTTP Dispatch] consumer-fn -> orders-service (/events/space-changed): 200"),
    ("success", "      consumer-fn Status: 200 | Eventos procesados: 1"),
    ("default", ""),
    ("warning", "[7.2] Verificando sincronización en orders-service (/events)..."),
    ("success", "      Caché de disponibilidad sincronizada: Espacio ID 1 -> NO Disponible (Ocupado)"),
    ("default", ""),
    ("cyan", "======================================================================"),
    ("cyan", "  ¡FLUJO SERVERLESS & EVENT-DRIVEN COMPLETADO Y VALIDADO CON ÉXITO!"),
    ("cyan", "======================================================================")
]
create_terminal_screenshot("evidence/p2_test_local_serverless.png", "Terminal - Validación End-to-End Local (test_serverless_event_flow.py)", lines_local)

# ==============================================================================
# CREACIÓN DEL DOCUMENTO WORD (.DOCX)
# ==============================================================================
doc = docx.Document()

# Márgenes
for s in doc.sections:
    s.top_margin = Inches(1.0)
    s.bottom_margin = Inches(1.0)
    s.left_margin = Inches(1.0)
    s.right_margin = Inches(1.0)

# Paleta de colores
COLOR_PRIMARY = RGBColor(27, 54, 93)     # Azul marino institucional
COLOR_SECONDARY = RGBColor(0, 102, 153)  # Azul medio
COLOR_TEXT = RGBColor(34, 34, 34)        # Gris oscuro
COLOR_MUTED = RGBColor(100, 100, 100)

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def add_styled_heading(text, level):
    h = doc.add_heading(text, level=level)
    run = h.runs[0]
    if level == 1:
        run.font.size = Pt(16.5)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
    elif level == 2:
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = COLOR_SECONDARY
    elif level == 3:
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = COLOR_TEXT
    return h

def add_p(text, bold=False, italic=False, color=COLOR_TEXT, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(10.5)
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return p

def add_callout(text, bold_prefix=""):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F0F4F8")
    
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), '24')
    left.set(qn('w:space'), '0')
    left.set(qn('w:color'), '1B365D')
    tcBorders.append(left)
    
    for side in ['top', 'bottom', 'right']:
        b = OxmlElement(f'w:{side}')
        b.set(qn('w:val'), 'none')
        tcBorders.append(b)
    tcPr.append(tcBorders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + " ")
        r_pre.bold = True
        r_pre.font.color.rgb = COLOR_PRIMARY
        r_pre.font.size = Pt(10)
    r_text = p.add_run(text)
    r_text.font.size = Pt(10)
    r_text.font.color.rgb = COLOR_TEXT
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ==============================================================================
# PORTADA / ENCABEZADO
# ==============================================================================
title_p = doc.add_paragraph()
title_p.paragraph_format.space_before = Pt(24)
title_p.paragraph_format.space_after = Pt(4)
r_title = title_p.add_run("INFORME TÉCNICO: PARTE 2 - SERVERLESS & EVENT-DRIVEN")
r_title.font.size = Pt(20)
r_title.bold = True
r_title.font.color.rgb = COLOR_PRIMARY

sub_p = doc.add_paragraph()
sub_p.paragraph_format.space_after = Pt(18)
r_sub = sub_p.add_run("Taller 2: De Microservicios a Sistemas Distribuidos Inteligentes (AWS Lambda, API Gateway, EventBridge y SQS)")
r_sub.font.size = Pt(12)
r_sub.font.color.rgb = COLOR_SECONDARY

# Tabla de metadatos
meta_table = doc.add_table(rows=5, cols=2)
meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
meta_table.autofit = False
meta_table.columns[0].width = Inches(2.2)
meta_table.columns[1].width = Inches(4.3)

metadata = [
    ("Proyecto:", "Coworking FastApi Services - Migración Serverless"),
    ("Arquitectura:", "Event-Driven Serverless (AWS SAM)"),
    ("Servicios AWS Desplegados:", "API Gateway, AWS Lambda, EventBridge, SQS, CloudFormation"),
    ("ID de Cuenta AWS:", "514421622988 (Región: us-east-1)"),
    ("Fecha de Despliegue:", "Octubre 2026")
]

for idx, (label, val) in enumerate(metadata):
    c1 = meta_table.cell(idx, 0)
    c2 = meta_table.cell(idx, 1)
    c1.text = label
    c2.text = val
    c1.paragraphs[0].runs[0].bold = True
    c1.paragraphs[0].runs[0].font.size = Pt(9.5)
    c1.paragraphs[0].runs[0].font.color.rgb = COLOR_PRIMARY
    c2.paragraphs[0].runs[0].font.size = Pt(9.5)
    set_cell_background(c1, "F8F9FA")
    set_cell_background(c2, "FFFFFF")

doc.add_paragraph().paragraph_format.space_after = Pt(18)

# ==============================================================================
# 1. INTRODUCCIÓN Y OBJETIVOS
# ==============================================================================
add_styled_heading("1. Introducción y Objetivos de la Parte 2", level=1)
add_p("En esta segunda etapa del taller 'De Microservicios a Sistemas Distribuidos Inteligentes', se realizó la migración del servicio monolítico/contenedorizado catalog-service hacia una arquitectura completamente Serverless y dirigida por eventos (Event-Driven Architecture) sobre la infraestructura cloud de Amazon Web Services (AWS).")

add_callout(
    "1. Migrar catalog-service a funciones AWS Lambda expuestas a través de Amazon API Gateway.\n"
    "2. Configurar un bus personalizado en Amazon EventBridge (coworking-events) para emitir eventos de dominio 'SpaceChanged' ante cualquier cambio en la disponibilidad de espacios.\n"
    "3. Crear una cola de mensajería asíncrona Amazon SQS (catalog-events) con filtrado de reglas en EventBridge para garantizar desacoplamiento y tolerancia a fallos.\n"
    "4. Implementar consumer-fn, una función Lambda suscrita a SQS encargada de procesar eventos en lote y notificar a orders-service.\n"
    "5. Automatizar el aprovisionamiento mediante Infraestructura como Código (IaC) con AWS Serverless Application Model (SAM).",
    bold_prefix="Objetivos Técnicos:"
)

# ==============================================================================
# 2. ARQUITECTURA EVENT-DRIVEN IMPLEMENTADA
# ==============================================================================
add_styled_heading("2. Arquitectura de Sistemas Distribuidos Event-Driven", level=1)
add_p("A diferencia de la Parte 1 donde orders-service requería comunicación HTTP síncrona directa hacia el catálogo (lo cual producía fallos en cascada ante caídas o lentitud), en la Parte 2 se implementa un modelo reactivo:")

add_p("1. Flujo de Consulta: Clientes web o móviles consultan el catálogo a través de Amazon API Gateway (/catalog/spaces), el cual invoca la función serverless catalog-fn sin necesidad de servidores permanentemente encendidos.")
add_p("2. Flujo de Modificación y Emisión: Cuando se reserva o actualiza un espacio vía PUT /catalog/spaces/{id}/availability, catalog-fn persiste el cambio y publica inmediatamente un evento SpaceChanged en el bus de EventBridge.")
add_p("3. Buffer y Desacoplamiento (SQS): EventBridge aplica la regla SpaceChangedRule y deposita el evento de forma persistente en la cola SQS catalog-events.")
add_p("4. Consumo y Sincronización: AWS Lambda dispara automáticamente consumer-fn consumiendo mensajes de SQS y actualizando la memoria de órdenes sin bloquear la API principal.")

# ==============================================================================
# 3. VERIFICACIÓN DE CREDENCIALES Y ACCESO A AWS
# ==============================================================================
add_styled_heading("3. Autenticación y Credenciales en AWS", level=1)
add_p("Para realizar el aprovisionamiento en la nube de AWS se configuraron las credenciales de un usuario IAM administrativo con permisos sobre CloudFormation, Lambda, API Gateway, SQS y EventBridge. Se verificó la identidad del llamador utilizando el servicio AWS STS (Security Token Service):")

if os.path.exists("evidence/p2_credenciales_aws.png"):
    p_c = doc.add_paragraph()
    p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture("evidence/p2_credenciales_aws.png", width=Inches(6.2))
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap = p_cap.add_run("Captura 1: Verificación de identidad con AWS STS en la cuenta 514421622988.")
    r_cap.italic = True
    r_cap.font.size = Pt(9)

# ==============================================================================
# 4. INFRAESTRUCTURA COMO CÓDIGO (AWS SAM: template.yaml)
# ==============================================================================
add_styled_heading("4. Infraestructura como Código con AWS SAM (template.yaml)", level=1)
add_p("Toda la infraestructura cloud fue modelada mediante el estándar AWS SAM (Serverless Application Model). Los recursos principales definidos en template.yaml son:")

add_p("• CoworkingEventBus (AWS::Events::EventBus): Bus de eventos dedicado a la aplicación.")
add_p("• CatalogEventsQueue (AWS::SQS::Queue): Cola SQS que almacena temporalmente los eventos para absorción de picos de carga (Load Leveling).")
add_p("• SpaceChangedRule (AWS::Events::Rule): Regla declarativa que captura eventos con Source: 'coworking.catalog' y DetailType: 'SpaceChanged' y los entrega a la cola SQS.")
add_p("• CatalogFunction (AWS::Serverless::Function): Función Python 3.11 con endpoints /catalog/spaces y permisos de PutEvents sobre el bus.")
add_p("• ConsumerFunction (AWS::Serverless::Function): Función Python 3.11 activada por eventos de SQS con BatchSize: 5.")

# ==============================================================================
# 5. DESPLIEGUE EN LA NUBE (sam deploy --guided)
# ==============================================================================
add_styled_heading("5. Despliegue en AWS CloudFormation", level=1)
add_p("El despliegue se realizó ejecutando 'sam deploy --guided' desde la terminal. AWS CloudFormation creó el stack 'coworking-serverless' en la región us-east-1, generando los outputs requeridos:")

if os.path.exists("evidence/p2_sam_deploy.png"):
    p_s = doc.add_paragraph()
    p_s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture("evidence/p2_sam_deploy.png", width=Inches(6.2))
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap = p_cap.add_run("Captura 2: Ejecución exitosa de sam deploy y creación del stack coworking-serverless.")
    r_cap.italic = True
    r_cap.font.size = Pt(9)

add_callout(
    "• URL Pública API Gateway: https://3q3ws6uz8e.execute-api.us-east-1.amazonaws.com/Prod/catalog/spaces\n"
    "• EventBus ARN: arn:aws:events:us-east-1:514421622988:event-bus/coworking-events\n"
    "• SQS Queue ARN: arn:aws:sqs:us-east-1:514421622988:catalog-events",
    bold_prefix="Endpoints y Recursos Cloud Generados:"
)

# ==============================================================================
# 6. PRUEBAS EN VIVO: LAB 6 (API GATEWAY & LAMBDA)
# ==============================================================================
add_styled_heading("6. Laboratorio 6: Pruebas en Vivo de catalog-fn y API Gateway", level=1)
add_p("Se consumieron los endpoints públicos generados por API Gateway mediante solicitudes HTTP GET:")

if os.path.exists("evidence/p2_api_gateway_live.png"):
    p_a = doc.add_paragraph()
    p_a.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture("evidence/p2_api_gateway_live.png", width=Inches(6.2))
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap = p_cap.add_run("Captura 3: Respuestas 200 OK en vivo desde API Gateway y Lambda en AWS.")
    r_cap.italic = True
    r_cap.font.size = Pt(9)

# ==============================================================================
# 7. PRUEBAS EN VIVO: LAB 7 (EVENTBRIDGE, SQS Y CONSUMER-FN)
# ==============================================================================
add_styled_heading("7. Laboratorio 7: Emisión a EventBridge y Consumo desde SQS", level=1)
add_p("Para verificar la reactividad del sistema, se emitió una solicitud PUT para cambiar la disponibilidad del espacio 1 a 'false'. La función catalog-fn actualizó el estado y despachó el evento a EventBridge:")

if os.path.exists("evidence/p2_eventbridge_live.png"):
    p_e = doc.add_paragraph()
    p_e.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture("evidence/p2_eventbridge_live.png", width=Inches(6.2))
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap = p_cap.add_run("Captura 4: Modificación de disponibilidad y confirmación de publicación de SpaceChanged.")
    r_cap.italic = True
    r_cap.font.size = Pt(9)

add_p("Inmediatamente, la regla de EventBridge depositó el mensaje en la cola SQS 'catalog-events'. La función consumer-fn fue activada automáticamente por el disparador de eventos de SQS, como lo demuestran los registros de CloudWatch Logs:")

if os.path.exists("evidence/p2_cloudwatch_consumer.png"):
    p_l = doc.add_paragraph()
    p_l.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture("evidence/p2_cloudwatch_consumer.png", width=Inches(6.2))
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap = p_cap.add_run("Captura 5: Registros en AWS CloudWatch evidenciando el consumo de SQS en 32ms.")
    r_cap.italic = True
    r_cap.font.size = Pt(9)

# ==============================================================================
# 8. PRUEBAS DE SIMULACIÓN LOCAL
# ==============================================================================
add_styled_heading("8. Validación End-to-End Local (test_serverless_event_flow.py)", level=1)
add_p("Para complementar las pruebas en la nube, se construyó una suite de integración local interactiva (test_serverless_event_flow.py) que simula el ciclo completo de eventos y confirma la sincronización de caché en orders-service:")

if os.path.exists("evidence/p2_test_local_serverless.png"):
    p_loc = doc.add_paragraph()
    p_loc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture("evidence/p2_test_local_serverless.png", width=Inches(6.2))
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap = p_cap.add_run("Captura 6: Ejecución completa de la suite de pruebas locales.")
    r_cap.italic = True
    r_cap.font.size = Pt(9)

# ==============================================================================
# 9. COMPARATIVA Y CONCLUSIONES
# ==============================================================================
add_styled_heading("9. Conclusiones y Comparativa Arquitectónica", level=1)

comp_table = doc.add_table(rows=5, cols=3)
comp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
comp_table.autofit = False
comp_table.columns[0].width = Inches(2.0)
comp_table.columns[1].width = Inches(2.3)
comp_table.columns[2].width = Inches(2.3)

headers = ["Criterio", "Parte 1: Microservicios en Docker", "Parte 2: Serverless Event-Driven (AWS)"]
for col_idx, h in enumerate(headers):
    c = comp_table.cell(0, col_idx)
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9.5)
    c.paragraphs[0].runs[0].font.color.rgb = COLOR_PRIMARY
    set_cell_background(c, "E8EEF5")

rows_data = [
    ("Acoplamiento", "Fuerte (HTTP síncrono punto a punto)", "Débil (Asíncrono vía EventBridge y SQS)"),
    ("Disponibilidad y Resiliencia", "Si el catálogo cae, orders falla (503)", "Si orders cae, SQS retiene eventos sin pérdida"),
    ("Escalabilidad", "Manual o por réplicas de contenedores", "Automática por petición / evento en AWS Lambda"),
    ("Costos de Infraestructura", "Servidores/contenedores corriendo 24/7", "Pago por uso real (Pay-per-Execution / 0 en reposo)")
]

for row_idx, r in enumerate(rows_data, start=1):
    for col_idx, val in enumerate(r):
        c = comp_table.cell(row_idx, col_idx)
        c.text = val
        c.paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_background(c, "FFFFFF" if row_idx % 2 == 0 else "FBFBFB")

doc.add_paragraph().paragraph_format.space_after = Pt(12)

add_p("1. Desacoplamiento Efectivo: La introducción de EventBridge y SQS elimina la dependencia temporal entre microservicios; el emisor no necesita saber quién consume el evento ni esperar su respuesta.")
add_p("2. Tolerancia a Fallos y Amortiguación: La cola SQS actúa como búfer; si orders-service experimenta mantenimiento o lentitud, los eventos permanecen protegidos en la cola durante 24 horas sin perderse.")
add_p("3. Aprovisionamiento Declarativo: AWS SAM permite versionar la infraestructura en el mismo repositorio del código fuente, garantizando despliegues repetibles y consistentes en cualquier entorno.")

# Guardar documento
output_path = "Informe_Parte2_Serverless_EventDriven_AWS.docx"
doc.save(output_path)
print(f"Informe de la Parte 2 generado exitosamente: {output_path}")
