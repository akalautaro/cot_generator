# COT Generator Script

Este es un script que en base a reportes e informes provenientes del programa SAP Business One, genera un archivo .txt formateado y listo para enviar a ARBA (Agencia de Recaudación Provincia de Buenos Aires).
El programa consiste, básicamente, en una conexión con diferentes consultas a la base de datos enlazada a nuestra cuenta de SAP Business One. Consultas con las cuales obtendrá los datos necesarios para completar el archivo que luego será enviado a ARBA.
Este script sigue en desarrollo constante.

## Comenzando 🚀

#### ¿Por qué COT Generator Script?

Este proyecto nace a partir de que en la empresa donde comencé a trabajar el primero de febrero de este año, se utiliza SAP Business One para la generación de los documentos de transporte, y a pesar de ser configurado una y otra vez, muchas veces tiene errores a la hora de crear los documentos, ya sea por falta o cruce de datos y por lo tanto, en una empresa donde se hacen tantos envíos por día y necesita del correcto funcionamiento de los eslabones, supone una enorme pérdida de tiempo (Y por lo tanto dinero).

#### ¿Qué es el COT?

COT significa “Código de Operación de Traslado o Transporte”. Es un régimen de información sobre el traslado o transporte de bienes en el territorio de la Ciudad Autónoma de Buenos Aires.

#### ¿Qué es ARBA?

La Agencia de Recaudación Provincia de Buenos Aires (ARBA) es una entidad autárquica de derecho público en el ámbito de la provincia de Buenos Aires, Argentina, que tiene por objeto la recaudación de impuestos provinciales.

#### ¿Quiénes están obligados a tramitar el COT?

El COT debe ser obtenido por los sujetos obligados a emitir comprobantes (facturas, remitos, guías o documentos equivalentes) que respalden el traslado y entrega de bienes (productos primarios o manufacturados), en forma previa al traslado o transporte de la mercadería, con origen y/o destino en esta jurisdicción.

_Las siguientes instrucciones te permitirán obtener una copia del proyecto en funcionamiento en tu máquina local para propósitos de desarrollo y pruebas.

### Pre-requisitos 📋

_Para que este script funcione vas a necesitar de:

* [SAP Business One](https://www.sap.com/latinamerica/products/business-one.html) - Es de donde saldrán los informes con los que se generará el archivo
* [HanaDB Client](https://www.sap.com/latinamerica/products/hana.html) - Cliente/tecnología de la base de datos.
* [Editor de texto](https://code.visualstudio.com/) - En mi caso utilicé Visual Studio Code
* [Librería DBApi](https://www.python.org/dev/peps/pep-0249/) - Más precisamente ```hdbcli```
* [Librería mechanize](https://pypi.org/project/mechanize/) - Necesaria para automatizar el proceso de subida de archivos a la web de ARBA
* [Librería xml.etree](https://docs.python.org/3/library/xml.etree.elementtree.html) - Necesaria para procesar la respuesta de ARBA
#### Recomendado
* [Gestor de base de datos](http://squirrel-sql.sourceforge.net/) - En mi caso utilicé SquirrelSQL

### Instalación 🔧

_Las mayores complicaciones pueden surgir a la hora de instalar las librerías, ya que las demás cosas necesarias poseen interfaces gráficas para realizar cada instalación.
Si sos un usuario que ya tiene experiencia con la programación e instalación de librerías, podés avanzar con el resto del readme._

* Librerías de Python

```
pip install dbapi
pip install hdbcli
pip install requests
pip install mechanize
```

## Construido con 🛠️

_Lo utilizado para construir este pequeño proyecto_

* [Python 3.8](https://www.python.org/) - Lenguaje de programación

## Contribuyendo 🖇️

_Si querés contribuir con este proyecto, no dudes en hacer una ```pull request```. Todas las ideas y sugerencias son bienvenidas!_

---
📱 En Twitter soy [akalautaro](www.twitter.com/akalautaro)

💻 por [akalautaro](https://github.com/akalautaro)
