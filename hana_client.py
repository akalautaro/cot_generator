from hdbcli import dbapi
import requests
import shutil
from mechanize import Browser

class HanaClient:
    conn = dbapi.Connection
    user = '********'
    passwd = '********'
    schema = '********'
    host = '********'
    port = 11111

    def __init__(self, user, passwd, schema):
        self.user = user
        self.passwd = passwd
        self.schema = schema
        self.conn = dbapi.connect(address=self.host, port=self.port, user=self.user, password=self.passwd)

        sql = "set schema " + self.schema
        cursor = self.conn.cursor()
        cursor.execute(sql)

    def get_documentos_de_transporte(self, fecha):
        
        sql = (f"""
                select otro."AbsEntry", otro."NextNum", otro."PostDate", otro."TranspNum",
                otro."Vehicle", otro."TrailerID", otro."Carrier", otro."IssueGate", 
                otro."WghtUnit", otro."WhsCode", owhs."WhsCode", 
                owhs."ZipCode" as "oZipCode", owhs."Street" as "oStreet", 
                owhs."StreetNo" as "oStreetNo", owhs."State" as "oState", 
                owhs."City" as "oCity", otro."TotalLC", otro."EDocExpFrm"
                from {self.schema}.otro inner join {self.schema}.owhs on otro."WhsCode" = owhs."WhsCode"
                where (\"PostDate\") >= {fecha}""") 

        cur = self.conn.cursor()
        cur.execute(sql)
        otro = self.list_to_dict(cur)
        cur.close()
        return otro

    def get_documentos_de_transporte_n(self, next_num, fecha='current_date'):
        
        sql = (f"""
                select otro."AbsEntry", otro."NextNum", otro."PostDate", otro."TranspNum",
                otro."Vehicle", otro."TrailerID", otro."Carrier", otro."IssueGate", 
                otro."WghtUnit", otro."WhsCode", owhs."WhsCode", 
                owhs."ZipCode" as "oZipCode", owhs."Street" as "oStreet", 
                owhs."StreetNo" as "oStreetNo", owhs."State" as "oState", 
                owhs."City" as "oCity", otro."TotalLC", otro."EDocExpFrm"
                from {self.schema}.otro inner join {self.schema}.owhs on otro."WhsCode" = owhs."WhsCode"
                where (otro."NextNum" = {next_num}) and (otro."PostDate" = {fecha})""") # Agregue parentesis

        cur = self.conn.cursor()
        cur.execute(sql)
        otro = self.list_to_dict(cur)
        cur.close()
        return otro

    @staticmethod
    def list_to_dict(cursor: dbapi.Connection.cursor):
        dict_rows = [dict(zip(list(zip(*cursor.description))[0], row)) for row in cursor.fetchall()]
        return dict_rows

    def get_docobjtype(self, abs):
        sql = (f"""
                select top 1 tro1."DocObjType" from {self.schema}.tro1
                where tro1."AbsEntry" = {abs}""") # Con TOP 1 traigo sólo el primer valor de la columna
        
        cur = self.conn.cursor()
        cur.execute(sql)
        doc_obj = self.list_to_dict(cur)
        cur.close()
        return doc_obj

    # Función-consulta para el formato Transportation Mapping Format (DocObjectType 13)
    # Extrae los datos para armar líneas 02 y 03
    def get_lineas_13(self, abs):
        
        sql = (f"""
                select oncm."NcmCode", inv1."InvQty",
                tro1."ItemCode", oitm."ItemName", inv1."UomCode",
                inv1."Quantity", oinv."PTICode", oinv."FolNumFrom", 
                oinv."Letter", inv1."ShipToCode", oinv."CardCode", 
                crd1."ZipCode" as "dZipCode", crd1."Street" as "dStreet", 
                crd1."StreetNo" as "dStreetNo", crd1."City" as "dCity", 
                crd1."State" as "dState", ocrd."Address", ocrd."ZipCode",
                ocrd."U_B1SYS_FiscIdType", ocrd."U_B1SYS_VATCtg",
                ocrd."LicTradNum" as "dLicTradNum", oinv."FolNumFrom", oinv."FolNumTo",
                oinv."CardName", oinv."DocEntry", oinv."DocNum", oinv."Letter", oinv."FolNumFrom"
                from {self.schema}.tro1
                left join {self.schema}.inv1 on tro1."DocEntry" = inv1."DocEntry" and tro1."DocLineNum" = inv1."LineNum" and tro1."DocObjType" = 13
                left join ( {self.schema}.oinv inner join {self.schema}.crd1 on oinv."CardCode" = crd1."CardCode" and oinv."ShipToCode" = crd1."Address" and crd1."AdresType" = 'S')
                on tro1."DocEntry" = oinv."DocEntry" and tro1."DocObjType" = 13
                inner join {self.schema}.oitm on tro1."ItemCode" = oitm."ItemCode"
                left join {self.schema}.oncm on oitm."NCMCode" = oncm."AbsEntry"
                inner join {self.schema}.ocrd on oinv."CardCode" = ocrd."CardCode"
                where tro1."AbsEntry" = {abs}""")

        cur = self.conn.cursor()
        cur.execute(sql)
        lineas = self.list_to_dict(cur)
        cur.close()
        return lineas

    # Función-consulta para el formato Generar COT (DocObjectType 67)
    # Extrae los datos para armar líneas 02 y 03
    def get_lineas_67(self, abs):
        
        sql = (f"""
                select oncm."NcmCode", wtr1."InvQty", tro1."ItemCode", oitm."ItemName",
                wtr1."UomCode", wtr1."Quantity", owtr."PTICode", owtr."FolNumFrom",
                owtr."Letter", wtr1."ShipToCode", owtr."CardCode", owtr."CardName",
                crd1."ZipCode" as "dZipCode", crd1."Street" as "dStreet", 
                crd1."StreetNo" as "dStreetNo", crd1."City" as "dCity", 
                crd1."State" as "dState", ocrd."Address", ocrd."ZipCode",
                ocrd."U_B1SYS_FiscIdType", ocrd."U_B1SYS_VATCtg",
                ocrd."LicTradNum" as "dLicTradNum", owtr."DocEntry", owtr."DocNum", owtr."Letter", owtr."FolNumFrom"
                from {self.schema}.tro1 
                left join {self.schema}.wtr1 on tro1."DocEntry" = wtr1."DocEntry" and tro1."DocLineNum" = wtr1."LineNum" and tro1."DocObjType" = 67
                left join ({self.schema}.owtr inner join {self.schema}.crd1 on owtr."CardCode" = crd1."CardCode" and owtr."ShipToCode" = crd1."Address" and crd1."AdresType" = 'S')
                on tro1."DocEntry" = owtr."DocEntry" and tro1."DocObjType" = 67
                inner join {self.schema}.oitm on tro1."ItemCode" = oitm."ItemCode"
                left join {self.schema}.oncm on oitm."NCMCode" = oncm."AbsEntry"
                inner join {self.schema}.ocrd on owtr."CardCode" = ocrd."CardCode"
                where tro1."AbsEntry" = {abs}""")

        cur = self.conn.cursor()
        cur.execute(sql)
        lineas = self.list_to_dict(cur)
        cur.close()
        return lineas