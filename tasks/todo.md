# Calculadora Hipoteca 2026 — Sesion 29-30 Abril 2026

## Completado

### Migración de diseño
- [x] Nuevo diseño (Mortgage_Calculator_2026.html) publicado como index.html principal
- [x] Versión anterior preservada como index_classic.html con su propia URL
- [x] README actualizado con tabla de versiones (Principal, Classic, V2, V1)

### Datos dinámicos
- [x] Añadido loadBankData() al nuevo diseño para cargar data/euribor.json y data/bank_offers.json
- [x] Añadido updateEuriborDisplay() para actualizar tipos BCE y Euríbor 12M
- [x] Verificado que la GitHub Action (update-bank-data.yml) actualiza ambas versiones via JSON compartidos
- [x] OFERTAS cambiado de const a let para permitir sobrescritura desde JSON

### Exportar / Compartir
- [x] PDF export funcional con html2canvas + jsPDF (captura #captureZone → A4 PDF)
- [x] WhatsApp: captura PNG + Web Share API (móvil) / descarga + texto (desktop)
- [x] Email: texto resumen via mailto
- [x] Eliminados TODOS los oklch() (80+ ocurrencias) → hex/rgba (html2canvas 1.4.1 no soporta oklch)
- [x] Botones share siempre se restauran tras captura (try/finally)

### UI / Estilos
- [x] Dark mode desactivado por defecto (darkMode: false)
- [x] Todos los valores euro auto-populados reseteados a 0 €
- [x] Demo prefill eliminado (no auto-carga 350k/80k)
- [x] Switches naranja solo cuando activos (no al revés)
- [x] Bonificación ITP Persona 1 y 2 activas por defecto
- [x] Títulos "Tipo y condiciones" y "Gastos fijos mensuales" — quitado font-size: 3px
- [x] Total gastos gestión: font-size 36px
- [x] Logo: icono calculadora (botones/grid, pantalla) 48x48px
- [x] Spacing cards resultados: gap 20px + margin-bottom en cards
- [x] Dividers naranja gradiente entre secciones del formulario
- [x] Fuente unificada: JetBrains Mono → -apple-system en TODA la UI
- [x] Amortización: placeholder 0€, resultados verde lime, botones verdes
- [x] Fondo beige #fafad5 (modo light)
- [x] Responsive completo: 4 breakpoints (1024/720/540px)

## Posibles next steps

- [ ] Mejorar dark mode con la nueva paleta hex (verificar contraste de todos los colores convertidos)
- [ ] Añadir persistencia local (localStorage) para guardar última simulación del usuario
- [ ] Mejorar la tabla comparativa: resaltar la fila seleccionada con color a juego
- [ ] Añadir gráfico visual de amortización (chart.js o similar)
- [ ] Optimizar para PWA: manifest.json + service worker para uso offline
- [ ] Añadir más bancos a las ofertas (actualmente 9-13 por tipo)
- [ ] Considerar migración del scraping de helpmycash a múltiples fuentes
- [ ] Testing cross-browser del PDF export (Safari, Firefox, mobile Chrome)
