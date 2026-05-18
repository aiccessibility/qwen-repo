# Dashboard de Monitoreo con Grafana - Configuración Completada

## 📊 Servicios Añadidos

### Prometheus
- **Puerto**: 9090
- **Función**: Recolección de métricas del backend y Celery
- **Endpoint de métricas**: `/metrics` en el backend

### Grafana
- **Puerto**: 3001 (para no confligir con el frontend en 3000)
- **Credenciales**: 
  - Usuario: `admin`
  - Password: `admin123`
- **Dashboards preconfigurados**: Accesibilidad Monitoring Dashboard

## 🚀 Cómo Usar

### 1. Iniciar todos los servicios
```bash
docker-compose up --build
```

### 2. Acceder a Grafana
- URL: http://localhost:3001
- Login: admin / admin123
- El dashboard "Accessibility Monitoring Dashboard" ya está configurado

### 3. Métricas Disponibles

El sistema ahora expone las siguientes métricas para Grafana:

#### Backend (FastAPI + Prometheus Instrumentator)
- `http_requests_total` - Total de peticiones HTTP
- `http_request_duration_seconds` - Duración de peticiones
- `http_requests_in_progress` - Peticiones en curso

#### API de Analytics (Endpoints nuevos)
- `/api/v1/analytics/statistics` - Estadísticas de auditorías
- `/api/v1/analytics/trends/violations` - Tendencias de violaciones
- `/api/v1/analytics/trends/compliance` - Historial de score de cumplimiento
- `/api/v1/analytics/monitors/status` - Estado de sitios monitoreados
- `/api/v1/analytics/realtime` - Métricas en tiempo real

### 4. Dashboards Incluidos

El dashboard preconfigurado incluye:

1. **Total Audits** - Estadísticas de auditorías en los últimos 30 días
2. **Active Audits** - Auditorías activas en tiempo real
3. **Violation Trends** - Gráfica de tendencias de violaciones por severidad
4. **Compliance Score History** - Evolución del score de cumplimiento
5. **Violations by Severity** - Distribución por severidad (pie chart)
6. **Recent Audit Results** - Tabla con resultados recientes

## 📈 Próximos Pasos Sugeridos

1. **Personalizar Dashboards**: Accede a Grafana y modifica las gráficas según tus necesidades
2. **Configurar Alertas**: Setup de alertas cuando el compliance score baje de cierto umbral
3. **Añadir Más Métricas**: Implementar métricas específicas de negocio en el backend
4. **Integrar con Frontend**: Consumir los endpoints de analytics desde el dashboard Next.js

## 🔧 Endpoints de Analytics

Todos los endpoints están documentados en Swagger:
- http://localhost:8000/docs

### Ejemplos de Uso:

```bash
# Estadísticas generales
curl http://localhost:8000/api/v1/analytics/statistics?days=30

# Tendencias de violaciones
curl http://localhost:8000/api/v1/analytics/trends/violations?days=30

# Score de cumplimiento
curl http://localhost:8000/api/v1/analytics/trends/compliance?days=30

# Estado de monitoreo continuo
curl http://localhost:8000/api/v1/analytics/monitors/status

# Métricas en tiempo real
curl http://localhost:8000/api/v1/analytics/realtime
```

## 🎯 Beneficios para tu MVP

✅ **Monitorización Continua Visual**: Dashboards profesionales para mostrar a clientes
✅ **Tendencias Históricas**: Gráficas de evolución de accesibilidad
✅ **Métricas en Tiempo Real**: Estado actual de auditorías y colas
✅ **Alertas Proactivas**: Configurable para notificaciones automáticas
✅ **White-Label Ready**: Fácil de personalizar para diferentes clientes
