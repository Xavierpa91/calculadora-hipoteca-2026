# Lessons Learned — Calculadora Hipoteca 2026

## html2canvas y oklch()
**Problema**: html2canvas 1.4.1 NO soporta la función CSS `oklch()`. Lanza error "Attempting to parse an unsupported color function" y toda la captura falla silenciosamente.
**Intentos fallidos**:
- Clonar DOM e inlinar computed styles → html2canvas parsea TAMBIÉN las hojas de estilo del documento, no solo los inline styles
- Desactivar `<style>` con `.disabled = true` → No impide que html2canvas lo lea
- Iframe aislado con html2canvas inyectado → Demasiado complejo y frágil
- SVG foreignObject → Tainted canvas por seguridad del navegador
**Solución definitiva**: Convertir TODOS los oklch a hex/rgba en el archivo fuente. Sin oklch en ningún sitio = html2canvas funciona a la primera, igual que en la versión classic.
**Regla**: Si usas html2canvas, NO uses oklch() ni ningún color CSS moderno (lab, lch, oklab). Solo hex, rgb, rgba, hsl.

## Botones de share desaparecen
**Problema**: capturarCards() ocultaba `.share-row` con `display: none` pero si html2canvas fallaba, nunca la restauraba.
**Solución**: Envolver siempre en try/finally para garantizar restauración del estado.

## CDN con defer + script inline
**Problema**: `<script src="..." defer>` carga async y ejecuta DESPUÉS del HTML. Si el `<script>` inline usa la librería, falla con "undefined".
**Solución**: Mover CDN al `<head>` SIN defer, o usar validación `typeof html2canvas === 'undefined'` antes de llamar.

## display: contents destruye gap
**Problema**: En mobile, `.results-col` usaba `display: contents` que destruye el contenedor flex y su `gap`.
**Solución**: Usar `display: flex; flex-direction: column; gap: 20px` en vez de `display: contents`.

## Valores hardcodeados en HTML exportado desde design tools
**Problema**: Al exportar desde herramientas de diseño (ej. v0/Claude Design), los HTML vienen con valores de ejemplo hardcodeados (350.000€, 1214€, font-size: 3px, etc.) y dark mode activado.
**Solución**: Revisar SIEMPRE: valores demo en spans/divs, placeholders en inputs, darkMode default, font-sizes raros (3px, 2px), y estilos inline que sobreescriben CSS (como switches con background-color naranja).
