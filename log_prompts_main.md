# Log de Prompts para main.py (SISAM-CUT)

Este documento contiene la lista cronológica de todos los prompts e instrucciones proporcionados para el desarrollo y evolución del archivo `main.py`.

---

## Fase 0: Concepción y Estructura de Datos (Inicios)
0. **Diseño de Base de Datos:** "Crea un script de Python llamado `setup_db.py` que genere una base de datos SQLite para un sistema de reportes de incidencias ambientales en el CUTonalá. Necesito una tabla llamada `incidencias` con campos para: tipo de contaminación (aire, agua, suelo, etc.), ubicación, descripción del problema, posibles responsables y acciones realizadas."
0.1 **Integridad de Datos:** "Asegúrate de que la base de datos esté bien estructurada y que podamos guardar la fecha de cada reporte automáticamente."

---

## Fase 1: Creación e Interfaz Base
1. **Inicio del Proyecto:** "Acabo de crear la base de datos sisam_cut.db. Por favor, genera el archivo main.py usando CustomTkinter que se conecte a esta base de datos. Asegúrate de que el sistema no permita borrar registros para cumplir con el requisito de integridad."
2. **Confirmación de Guardado:** "los datos ingresados se guardan en la base de datos?"
3. **Detalles y Mapas:** "agrega un boton que sea ver detalles en el menu ver incidencias que cuando lo presiones te salga los detalles como la descripcion y acciones realizadas y ademas que la ubicacion se por geolocalizacion, cuando el usuario presione la opcion ubicaion exacta, te pida permiso para acceder a la ubicacion y obtener las coordenadas automaticas, en la pantalla despues de dar el permiso aparecera un mapa en la que diga tu ubicacion actual, ademas que pregunte si tu ubicacion actual es donde ocurrio la incidencia, le das a la opcion \"si\" o en su defecto un boton de ajustar ubicacion por si no se encuentra en la ubicacion donde ocurrio la incidencia, esto ultimo con un pin por el mapa"
4. **Corrección de Carga de Mapa:** "caundo abres el mapa aparece todo en blanco, cambia eso"
5. **Lógica de Permisos:** "caundo aceptas dar tus coordenadas aparece en una ubicacion que no es la mia y cuando le das a no te sigue abriendo el mapa, agrega que si le das a no, no se abra nada"
6. **Ubicación Predeterminada:** "que la ubicacion por default sea en el cut tonala"

---

## Fase 2: Evidencia Fotográfica y Dashboard
7. **Fotos (1/3):** "en registro de incidencias agrega que sea posible agregar evidencia fotografica, que no sea obligatoria, y que aparezca en detalles cuando la agregas"
8. **Fotos (3/3):** "puedes poner que puedas agregar hasta tres imagenes"
9. **Dashboard Visual:** "quiero que cuando el usuario abra la app no vea directamente la lista de incidentes haz que la pantalla sea un dashboard visual, que incluir: cuadros de resumen (ej. total de reportes este mes: 15) graficas, una grafica pastel que muestre los incidentes en ella, y mas cosas que se te ocurran"
10. **Diseño de Dashboard:** "para el fondo de las tres tarjetas utiliza el mismo gris que usaste para ultimos reportes y la grafica de pastel ademas utiliza colores pastel para la grafica y que el color tenga que ver con el incidente"
11. **Ajuste de Colores:** "colores mas vibrantes"

---

## Fase 3: Mapa de Calor (Experimental)
12. **Implementación:** "agrega una seccion de mapa de calor, Un mapa a pantalla completa del CUTonalá con manchas de calor (rojo, amarillo, verde) donde se han hecho los reportes."
13. **Navegación y Claridad:** "es muy facil perderte en el mapa agrega algo que si te mueves de la ubicaion te vuelva a centrar en el cut y siento que no es muy claro los colores del mapa"
14. **Remoción:** "quita lo del mapa de calor"

---

## Fase 4: Reportes PDF y Pulido de UI
15. **Centro de Reportes:** "agrega un centro de generacion de reportes, Crea una pestaña exclusiva para descargar la información, en lugar de solo verla en la pantalla. que incluya un filtro por fecha y un boton para descargar el reporte mensual en un pdf, esto ultimo que sea solo texto"
16. **Orden del Menú:** "el boton para generar el reporte esta muy abajo, que quede debajo del boton ver incidentes"
17. **Limpieza de UI:** "en el menu lateral hay un texto en medio que no tiene ningun sentido, el texto dice \"tema:\""

---

## Fase 5: Migración a MariaDB y Sesiones
18. **Cambio de DB:** "necesito cambiar a una base datos en maria db"
19. **Credenciales:** "host: 127.0.0.1 usuario: root contraseña: root Nombre de la Base de Datos: SISAM la base de datos ya existe"
20. **Sistema de Usuarios:** "puedes crear un inicio de sesion, que se necesite un nombre, correo y contraseña, no necesito que se valide que el correo sea verdadero, una vez que ya iniciaste sesion no sea necesario volver a hacerlo, tambien crea una funcion llamada perfil donde aparezcan tus datos asi como tus reportes de incidencias, y una opcion para cerrar la sesion, registralos con el rol de alumno"
21. **Flujo de Sesión:** "cuando le des al boton de cerrar sesion preguntale si quiere cerrar la sesion, no lo hagas directamente, y cuando creas una nueva cuenta te meta a la app, que no sea necesario volver a poner el correo y la contraseña"
22. **Ajuste Visual Login:** "cuando cierras la sesion el cuadro de inicio de sesion no queda en su lugar"

---

## Fase 6: Roles Administrativos y Gestión
23. **Cuentas de Administrador:** "necesito que hagas una opcion para crear cuenta para administradores, que solo te pida nombre y una contraseña que sera 2510, que el rol de administrador pueda borrar usuarios, borrar incidencias o modificarlas, y que el administrador pueda borrar otros administradores, que los usuarios y administradores aparezcan en una pestaña llamada usuarios y que solo los admin puedan verla"
24. **Privacidad y Layout:** "que no diga cual es la contraseña de admin y arregla la distribucion de la palabra tema"
25. **Login de Admin y UI:** "cuando cierras la sesion de admin e intentas volver a iniciar sesion con la cuenta ya creada de admin, no te deja, ni con la contraseña personal ni con el codigo 2510, haz que para iniciar la sesion como admin solo necesites la contraseña personal y el nombre, y cambia el color del boton usuarios al mismo color de los demas"
