#!/usr/bin/env python3
import argparse
import sys
import datetime
from datetime import datetime
import requests
import os
import shutil
from mechanize import Browser
import xml.etree.ElementTree as ET

from hana_client import HanaClient

# Argumentos: usuario, password, schema BD
hana = HanaClient('********', '********', '********')

# Argumentos
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fecha', help='Fecha para la cual generar los cot formato aaaa-mm-dd (por defecto la fecha actual)')
parser.add_argument('-n', '--nextnum', help='Numero consecutivo si se quiere generar un cot en particular (hay que indicar fecha)')
args = parser.parse_args()
fecha = {args.fecha}
next_num = {args.nextnum}

try:
    os.mkdir('COT Generados')
except Exception as e:
    pass

os.makedirs('COT Generados/Enviados', exist_ok=True)
os.makedirs('COT Generados/Error', exist_ok=True)

if args.fecha is not None:
    fecha = str(args.fecha)
    fecha = (f"'{fecha[0:4]}-{fecha[4:6]}-{fecha[6:8]}'")

elif args.fecha is None:
    fecha_actual = datetime.now()
    fecha_actual = str(fecha_actual.strftime('%Y%m%d'))
    fecha = (f"'{fecha_actual[0:4]}-{fecha_actual[4:6]}-{fecha_actual[6:8]}'")

# Buscar los OTRO (Encabezados de documento de transporte)
# Si fecha y next num son argumentos, sólo generará ese cot
if len(next_num) > 2:
    otro = hana.get_documentos_de_transporte_n(next_num, fecha)
    pass
# Si recibe fecha como argumento, generará todos los cot para esa fecha (por defecto es la fecha actual)
else:
    otro = hana.get_documentos_de_transporte(fecha)
    pass

# Estos contadores son para saber la cantidad de cot, no tienen otra función
contador_corr = 0   
contador = 0

cant_remitos = 0
for o in otro:
    print('--------------------------------------------------------')
    contador += 1
    # Verifico si tiene número de transporte
    t = o.get("TranspNum")
    cot = 0
    try:
        cot = int(t)
    except Exception as e:
        pass
    if cot != 0:
        print(f"Documento {o.get('NextNum')} ya autorizado, COT: {cot}")
        continue
    # No tiene número de transporte leo las líneas
    next_num = o.get('NextNum') # Nro Consecutivo
    next_num_nombre = str(next_num).zfill(6)
    print(f"Documento {o.get('NextNum')} no autorizado")
    abs_entry = o.get("AbsEntry")
    print(t)
    postdate = o.get("PostDate").strftime('%Y%m%d') # Fecha del día formateada
    abs_entry_nombre = str(abs_entry).zfill(6) # AbsEntry formateado completando con 0 a la izquierda

    # Averiguo tipo de documento
    doc_lines = hana.get_docobjtype(abs_entry)
    doc_type = 0
    for d in doc_lines:
        doc_type = d.get("DocObjType")# Tipo de dato int

    # Fecha actual: se puede utilizar para hacer la consulta get_documentos_de_transporte()
    fecha_actual = datetime.now()
    fecha_actual = fecha_actual.strftime('%Y%m%d')  # También se puede usar para evitar posibles problemas  
                                                    # con PostDates anteriores a la hora de armar las líneas 02

    # Hora de salida = hora_actual
    # hora_actual = datetime.now()
    # hora_actual = hora_actual.strftime('%H%M')
    hora_actual = '' # Hardcodeado. No es obligatorio
    
    almacen_salida = o.get("WhsCode")[-3:]
    puerta_salida = str(o.get("IssueGate")).zfill(3)

    # Archivo de texto
    f = open (f'./COT Generados/TB_********_{almacen_salida}{puerta_salida}_{postdate}_{next_num_nombre}.txt','w')

    # TIPO REGISTRO LÍNEA 01 |---->
    f.write('01|********\n')
    
    fol_num_comp = ''
    cant_remitos = 0

    if doc_type == 13:
        lineas_13 = hana.get_lineas_13(abs_entry)
        for l in lineas_13:
            fol_num = str(l.get('FolNumFrom')) # Si nro de folio cambia, escribe una nueva línea 02
            if fol_num != fol_num_comp:
                afip = l.get("Letter")
                if afip == 'A':
                    afip = '001'
                elif afip == 'B':
                    afip = '006'
                elif afip == 'R':
                    afip = '091'
                elif afip == 'E':
                    afip = '001'
                elif afip == None:    # Hardcode para testing
                    afip = '001'      # Puede ser también 091   
                pti_code = str(l.get("PTICode")).zfill(5)
                fol_number = str(l.get("FolNumFrom")).zfill(8)

                cod_unico = afip + pti_code + fol_number

                dest_dni = ''
                dest_cuit = l.get("dLicTradNum")
                dest_razon_social = l.get("CardName")

                tipo_doc = l.get("U_B1SYS_FiscIdType")
                if tipo_doc == '80' or tipo_doc == '999':
                    tipo_doc = 'CI'
                elif tipo_doc == '94':
                    tipo_doc = 'PAS'
                elif tipo_doc == '96':
                    tipo_doc = 'DNI'
                tipo_doc = '' # Puede estar hardcodeado
                cons_final = l.get("U_B1SYS_VATCtg") # Ignorar CF
                if cons_final == 'CF':
                    cons_final = 1
                else:
                    cons_final = 0
                dest_tenedor = '0'
                if cons_final == 1:
                    dest_tenedor = '0'
                dest_calle = l.get("dStreet")
                if len(dest_calle) > 40:
                    dest_calle = dest_calle[0:40] # Longitud de la cadena limitada por ARBA a 40 carac.
                dest_num = l.get("dStreetNo")
                if dest_num == 'S/N' or dest_num == '0' or dest_num == '' or dest_num is None:
                    dest_num = '' 
                    dest_comple = 'S/N'
                else:
                    dest_comple = ''
                # Líneas en blanco pueden borrarse una vez que esté terminada la extracción de datos
                dest_piso = ''
                dest_depto = ''
                dest_barrio = ''
                dest_cp = l.get("dZipCode")
                dest_localidad = l.get("dCity")
                # Diccionario para obtener código provincia
                dicc_prov = {'00' : 'C', '01' : 'B', '02' : 'K', '03' : 'X', '04' : 'W', '05' : 'E', '06' : 'Y', 
                            '07' : 'M', '08' : 'F', '09' : 'A', '10' : 'J', '11' : 'D', '12' : 'Z', '13' : 'S', 
                            '14' : 'G', '15' : 'T', '16' : 'H', '17' : 'U', '18' : 'P', '19' : 'N', '20' : 'Q', 
                            '21' : 'L', '22' : 'R', '23' : 'V', '24' : ''}
                dest_provincia = dicc_prov[str(l.get('dState'))]
                prop_destino_domicilio_cod = ''
                entrega_domicilio_origen = 'NO' # Por lo gral es No
                orig_cuit = "********"
                orig_razon_social = '********' # Hardcodeado
                emisor_tenedor = '0' # Por lo gral, NO
                orig_calle = o.get("oStreet")
                orig_num = o.get("oStreetNo")
                if orig_num == 'S/N' or orig_num == '0' or orig_num == '' or orig_num is None:
                    orig_num = '' 
                    orig_comple = 'S/N'
                else:
                    orig_comple = ''
                orig_piso = ''
                orig_depto = ''
                orig_barrio = ''
                orig_cp = o.get("oZipCode")
                orig_localidad = o.get("oCity")
                orig_provincia = dicc_prov[str(o.get('oState'))]
                trans_cuit = str(o.get('Carrier')) # Devuelve cuit en formato P1234567890
                trans_cuit = trans_cuit.replace('P', '') # Elimino la P formateando de manera correcta
                tipo_reco = ''
                reco_localidad = ''
                reco_calle = ''
                reco_ruta = ''
                patente = o.get("Vehicle")
                trailer = o.get("TrailerID")
                if trailer is None:
                    trailer = ''
                produc_no_term = '0' # Hardcodeado 'No'
                importe = str(o.get("TotalLC"))
                importe_cot = importe.replace('.', '').zfill(14) # Importe formateado

                fol_num_comp = fol_num

                # Línea 02 terminada
                f.write(f"""02|{postdate}|{cod_unico}|{fecha_actual}|{hora_actual}|E|{cons_final}|\
                {tipo_doc}|{dest_dni}|{dest_cuit}|{dest_razon_social}|{dest_tenedor}|{dest_calle}|\
                {dest_num}|{dest_comple}|{dest_piso}|{dest_depto}|{dest_barrio}|{dest_cp}|{dest_localidad}|\
                {dest_provincia}|{prop_destino_domicilio_cod}|{entrega_domicilio_origen}|{orig_cuit}|\
                {orig_razon_social}|{emisor_tenedor}|{orig_calle}|{orig_num}|{orig_comple}|{orig_piso}|\
                {orig_depto}|{orig_barrio}|{orig_cp}|{orig_localidad}|{orig_provincia}|{trans_cuit}|\
                {tipo_reco}|{reco_localidad}|{reco_calle}|{reco_ruta}|{patente}|{trailer}|\
                {produc_no_term}|{importe_cot}|\n""")

        
                cant_remitos += 1 # Cada línea 02 cuenta como remito

            # TIPO REGISTRO LÍNEAS 03 |---->
            """
            03: Hardcodeado
            Codigo Unico: NcmCode formateado
            Codigo unidad de medida: WghtUnit
            Cantidad: UomCode x CantAjustada
            Codigo prod: ItemCode
            Nombre prod: ItemName -> formateado a descrip_prod
            Unidad de medida: UoMCode
            Cant. ajustada: Quantity
            """

            ncm_code = l.get('NcmCode').replace('KG', '')
            unidad_medida = o.get('WghtUnit')
            item_code = l.get('ItemCode')
            uom_code = l.get('UomCode')
            cantidad = 1 # Inicializo cantidad
            
            cant_ajustada = int(l.get("Quantity")) # Hago la consulta una sola vez 
            if l.get('UomCode') == 'UN':
                uom_code_mult = 100
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 12':
                uom_code_mult = 1200
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 8':
                uom_code_mult = 800
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 6':
                uom_code_mult = 600
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 14':
                uom_code_mult = 1400
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 18':
                uom_code_mult = 1800
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 24':
                uom_code_mult = 2400
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'Pallet':
                uom_code_mult = 1
                cantidad = cant_ajustada * uom_code_mult

            descrip_prod = str(l.get('ItemName'))
            if (len(descrip_prod)) >= 40:
                descrip_prod = descrip_prod[0:40] # Longitud de la cadena limitada por ARBA a 40 carac.

            # Líneas 03 terminadas con todos los datos recogidos
            f.write(f"03|{ncm_code}|{unidad_medida}|{cantidad}|{item_code}|{descrip_prod}|{uom_code}|{cant_ajustada}00\n")

    elif doc_type == 67:
        lineas_67 = hana.get_lineas_67(abs_entry)
        for l in lineas_67:
            fol_num = str(l.get('FolNumFrom')) # Si nro de folio cambia, escribe una nueva línea 02
            if fol_num != fol_num_comp:
                afip = l.get("Letter")
                if afip == 'A':
                    afip = '001'
                elif afip == 'B':
                    afip = '006'
                elif afip == 'R':
                    afip = '091'
                elif afip == 'E':
                    afip = '001'
                elif afip == None:    # Hardcode para testing
                    afip = '001'      # Puede ser también 091   
                pti_code = str(l.get("PTICode")).zfill(5)
                fol_number = str(l.get("FolNumFrom")).zfill(8)

                cod_unico = afip + pti_code + fol_number

                dest_dni = ''
                dest_cuit = l.get("dLicTradNum")
                dest_razon_social = l.get("CardName")

                tipo_doc = l.get("U_B1SYS_FiscIdType")
                if tipo_doc == '80' or tipo_doc == '999':
                    tipo_doc = 'CI'
                elif tipo_doc == '94':
                    tipo_doc = 'PAS'
                elif tipo_doc == '96':
                    tipo_doc = 'DNI'
                tipo_doc = '' # Puede estar hardcodeado
                cons_final = l.get("U_B1SYS_VATCtg") # Ignorar CF
                if cons_final == 'CF':
                    cons_final = 1
                else:
                    cons_final = 0
                dest_tenedor = '0'
                if cons_final == 1:
                    dest_tenedor = '0'
                dest_calle = l.get("dStreet")
                if len(dest_calle) > 40:
                    dest_calle = dest_calle[0:40] # Longitud de la cadena limitada por ARBA a 40 carac.
                dest_num = l.get("dStreetNo")
                if dest_num == 'S/N' or dest_num == '0' or dest_num == '' or dest_num is None:
                    dest_num = '' 
                    dest_comple = 'S/N'
                else:
                    dest_comple = ''
                # Líneas en blanco pueden borrarse una vez que esté terminada la extracción de datos
                dest_piso = ''
                dest_depto = ''
                dest_barrio = ''
                dest_cp = l.get("dZipCode")
                dest_localidad = l.get("dCity")
                # Diccionario para obtener código provincia
                dicc_prov = {'00' : 'C', '01' : 'B', '02' : 'K', '03' : 'X', '04' : 'W', '05' : 'E', '06' : 'Y', 
                            '07' : 'M', '08' : 'F', '09' : 'A', '10' : 'J', '11' : 'D', '12' : 'Z', '13' : 'S', 
                            '14' : 'G', '15' : 'T', '16' : 'H', '17' : 'U', '18' : 'P', '19' : 'N', '20' : 'Q', 
                            '21' : 'L', '22' : 'R', '23' : 'V', '24' : ''}
                dest_provincia = dicc_prov[str(l.get('dState'))]
                prop_destino_domicilio_cod = ''
                entrega_domicilio_origen = 'NO' # Por lo gral es No
                orig_cuit = "********"
                orig_razon_social = '********' # Hardcodeado
                emisor_tenedor = '0' # Por lo gral, NO
                orig_calle = o.get("oStreet")
                orig_num = o.get("oStreetNo")
                if orig_num == 'S/N' or orig_num == '0' or orig_num == '' or orig_num is None:
                    orig_num = '' 
                    orig_comple = 'S/N'
                else:
                    orig_comple = ''
                orig_piso = ''
                orig_depto = ''
                orig_barrio = ''
                orig_cp = o.get("oZipCode")
                orig_localidad = o.get("oCity")
                orig_provincia = dicc_prov[str(o.get('oState'))]
                trans_cuit = str(o.get('Carrier')) # Devuelve cuit en formato P1234567890
                trans_cuit = trans_cuit.replace('P', '') # Elimino la P formateando de manera correcta
                tipo_reco = ''
                reco_localidad = ''
                reco_calle = ''
                reco_ruta = ''
                patente = o.get("Vehicle")
                trailer = o.get("TrailerID")
                if trailer is None:
                    trailer = ''
                produc_no_term = '0' # Hardcodeado 'No'
                importe = str(o.get("TotalLC"))
                importe_cot = importe.replace('.', '').zfill(14) # Importe formateado

                fol_num_comp = fol_num

                # Línea 02 terminada
                f.write(f"""02|{postdate}|{cod_unico}|{fecha_actual}|{hora_actual}|E|{cons_final}|\
                {tipo_doc}|{dest_dni}|{dest_cuit}|{dest_razon_social}|{dest_tenedor}|{dest_calle}|\
                {dest_num}|{dest_comple}|{dest_piso}|{dest_depto}|{dest_barrio}|{dest_cp}|{dest_localidad}|\
                {dest_provincia}||{entrega_domicilio_origen}|{orig_cuit}|\
                {orig_razon_social}|{emisor_tenedor}|{orig_calle}|{orig_num}|{orig_comple}|{orig_piso}|\
                {orig_depto}|{orig_barrio}|{orig_cp}|{orig_localidad}|{orig_provincia}|{trans_cuit}|\
                {tipo_reco}|{reco_localidad}|{reco_calle}|{reco_ruta}|{patente}|{trailer}|\
                {produc_no_term}|{importe_cot}|\n""")

        
                cant_remitos += 1 # Cada línea 02 cuenta como remito

            # TIPO REGISTRO LÍNEAS 03 |---->
            """
            03: Hardcodeado
            Codigo Unico: NcmCode formateado
            Codigo unidad de medida: WghtUnit
            Cantidad: UomCode x CantAjustada
            Codigo prod: ItemCode
            Nombre prod: ItemName -> formateado a descrip_prod
            Unidad de medida: UoMCode
            Cant. ajustada: Quantity
            """

            ncm_code = l.get('NcmCode').replace('KG', '')
            # unidad_medida = o.get('WghtUnit') # Puede hardcodearse ya que no hay otra
            unidad_medida = '3'
            item_code = l.get('ItemCode')
            uom_code = l.get('UomCode')
            cantidad = 1 # Inicializo cantidad
            
            cant_ajustada = int(l.get("Quantity")) # Hago la consulta una sola vez 
            if l.get('UomCode') == 'UN':
                uom_code_mult = 100
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 12':
                uom_code_mult = 1200
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 8':
                uom_code_mult = 800
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 6':
                uom_code_mult = 600
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 14':
                uom_code_mult = 1400
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 18':
                uom_code_mult = 1800
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'BULTO x 24':
                uom_code_mult = 2400
                cantidad = cant_ajustada * uom_code_mult
            elif l.get('UomCode') == 'Pallet':
                uom_code_mult = 1
                cantidad = cant_ajustada * uom_code_mult

            descrip_prod = str(l.get('ItemName'))
            if (len(descrip_prod)) >= 40:
                descrip_prod = descrip_prod[0:40] # Longitud de la cadena limitada por ARBA a 40 carac.

            # Líneas 03 terminadas con todos los datos recogidos
            f.write(f"03|{ncm_code}|{unidad_medida}|{cantidad}|{item_code}|{descrip_prod}|{uom_code}|{cant_ajustada}00\n")

    # La línea Footer 04 tiene que contar las líneas 02 del documento
    f.write(f'04|{(str(cant_remitos)).zfill(2)}\n')

    # shutil.copy(f, gen.path())
    
    # Si todo sale bien y el archivo existe
    print(f'COT nº: {next_num_nombre} creado con éxito')

    contador_corr += 1

    print("\nEnviando formulario...")
    browser = Browser()
    browser.open("https://cot.arba.gov.ar/TransporteBienes/pages/remitos/PresentarRemitos.jsp")
    form = browser.select_form("presentarRemitosForm")
    browser["user"] = "********"
    browser["password"] = "********"
    browser.form.add_file(open(f'./COT Generados/TB_********_{almacen_salida}{puerta_salida}_{postdate}_{next_num_nombre}.txt','rb'), 'text/plain', f'TB_********_{almacen_salida}{puerta_salida}_{postdate}_{next_num_nombre}.txt', name='file')
    response = browser.submit()

    texto = response.get_data() # Devuelve response en bytes
    txt = texto.decode("LATIN1") # Paso a <str>

    # Armo un .xml con el <str> txt
    root = ET.fromstring(txt)

    for nodo in root.iter('validacionesRemitos'):
        for elemento in nodo.iter():
            # Descarto las líneas que no me interesan
            if elemento.tag == 'remito' or elemento.tag == 'errores' or elemento.tag == 'error' or elemento.tag == 'validacionesRemitos':
                pass
            else:
                print(f"{elemento.tag}: {elemento.text}")

    f.close()

print('--------------------------------------------------------')
print(f'Total COT: {contador}')
print(f'Total COT corregidos: {contador_corr}')
print('------------------------')