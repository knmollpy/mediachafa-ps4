# MediaChafa PS4

**Sitio oficial:** [mediachafa-transfer.vercel.app](https://mediachafa-transfer.vercel.app/)

MediaChafa es una biblioteca web y Android para organizar archivos, enlaces y un catálogo de juegos de PS4, La app móvil tiene una interfaz sencilla a teléfonos

## Descargar la aplicación

- **Android (2.5.3):** [Descargar APK directamente](https://mediachafa-transfer.vercel.app/downloads/MediaChafa.apk?v=2.5.1)
- **Versión web:** [Abrir MediaChafa](https://mediachafa-transfer.vercel.app/)

Descargá el APK y abrilo en Android para instalarlo. En la app podés elegir si querés que recuerde tu sesión; también podés cerrarla en cualquier momento

## Cómo funciona y qué opciones tiene

- **Archivos y carpetas:** navegar la biblioteca, crear carpetas y subir o descargar archivos según los permisos de cada cuenta
- **Enlaces:** guardar, ordenar, compartir y borrar enlaces permitidos.
- **Espacio de almacenamiento:** consultar el espacio usado en Google Drive y Cloudflare R2
- **Juegos PS4:** catálogo con portadas, carpetas, descripciones y características. Al abrir un juego se muestran sus detalles; sus enlaces se pueden descargar o compartir
- **Invitados:** acceso directo solo al catálogo público de PS4. Pueden consultar títulos, compartir enlaces y reportar enlaces caídos; no pueden administrar juegos ni entrar a los archivos
- **Reportes y DM:** los reportes de enlaces caídos llegan a DM, apartado disponible solo para el equipo
- **Usuarios:** el equipo crea colaboradores con acceso completo y usuarios normales con permisos elegidos para ver archivos y carpetas públicas, acceder a enlaces o Juegos PS4, crear carpetas, subir archivos y usar una cuota configurada
- **Privacidad:** los permisos también se aplican en Supabase; la interfaz no es el único control de acceso
- **Sesión:** la app permite recordar usuario y sesión en el dispositivo o cerrar sesión y volver al inicio

## Servicio de almacenamiento

se ofrece **20 GB de almacenamiento por US$ 5 con acceso permanente**, sujeto a disponibilidad y a las condiciones acordadas al contratarlo. Para consultar, usá el [sitio oficial](https://mediachafa-transfer.vercel.app/) o contactar por el reporte de enlaces caidos

## Tecnología

La aplicación web y Android usa Capacitor; Supabase gestiona autenticación y datos, mientras Cloudflare R2 y Google Drive se pueden usar como destinos de almacenamiento. El catálogo muestra los enlaces configurados por el equipo
