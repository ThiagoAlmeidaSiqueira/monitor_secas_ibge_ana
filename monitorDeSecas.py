#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
   
#http://200.129.31.16/map/mapa-monitor/sig
#http://200.129.31.16/uploads/mapas/agosto2019.zip


#https://mapas.ibge.gov.br/bases-e-referenciais/bases-cartograficas/malhas-digitais
#ftp://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2015/
#ftp://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2015/Brasil/BR/br_municipios.zip

#ftp://geoftp.ibge.gov.br/organizacao_do_territorio/redes_e_fluxos_geograficos/gestao_do_territorio/bases_de_dados/xls/Base_de_dados_dos_municipios.xls

from shapely.geometry import shape, mapping
import fiona
import xlrd 

import requests
from lxml import html
import ftplib
# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import shutil
import datetime
import re

import zipfile

import json


def shapeIntersects(seca,ibge,planilha):
    muni = listaMunicipios(planilha)
    municipios = list()
    for popu in fiona.open(seca):
        seca = popu['properties']
        valor = None
        if 'Valor' in seca.keys():
            valor = seca['Valor']
        intensidade = None
        if 'uf_codigo' in seca.keys(): 
            intensidade = seca['uf_codigo']
        elif 'Uf_Codigo' in seca.keys():
            intensidade = seca['Uf_Codigo']
        else:
            intensidade = seca['Ind']
        intensidadeNumero = int(intensidade.replace('s','').replace('i','-1'))
        for crim in fiona.open(ibge):
            municipio = crim['properties']
            nome = municipio['NM_MUNICIP']
            codigo = int(municipio['CD_GEOCMU'])
            if shape(crim['geometry']).intersects(shape(popu['geometry'])):
                #print(nome+','+str(codigo)+','+str(valor)+','+intensidade+','+str(intensidadeNumero))
                registro = dict()
                r = [m for m in municipios if m['codigo']==codigo]
                if len(r)==1:
                    if intensidadeNumero > r[0]['intensidadeNumero']:
                        registro = r[0]
                    else:
                        break
                registro['nome']=nome
                registro['codigo']=codigo
                registro['valor']=str(valor)
                registro['intensidade']=intensidade
                registro['intensidadeNumero']=intensidadeNumero
                registro['uf']=None
                ### PEGA UF DA PLANILHA #############################
                mun = [m for m in muni if m['Codmundv']==codigo]
                if len(mun)==1:
                    registro['uf']=mun[0]['UF']
                #####################################################
                if len(r)==0:
                    municipios.append(registro)
    return municipios


def listaMunicipios(planilha):
    municipios = list()
    loc = (planilha) 
    wb = xlrd.open_workbook(loc) 
    sheet = wb.sheet_by_index(0) 
    sheet.cell_value(0, 0) 
    for i in range(1,sheet.nrows,1):
        registro = dict()
        registro['UF']=sheet.cell_value(i, 0)
        registro['CodUF']=sheet.cell_value(i, 1)
        registro['Codmundv']=int(sheet.cell_value(i, 2))
        registro['NomeMunic']=sheet.cell_value(i, 4)
        municipios.append(registro)
    return municipios

def salvaArquivo(lista,ano,mes):
    diretorio = "saida/"
    if not os.path.exists(diretorio):
        os.makedirs(diretorio)
    f = open(diretorio+ano+"_"+mes+"_monitor_secas.csv", "w")
    f.write('nome,codigo,valor,intensidade,uf\n')
    for registro in lista:
        f.write(registro['nome']+','+str(registro['codigo'])+','+str(registro['valor'])+','+registro['intensidade']+','+registro['uf']+'\n')
    f.close()


def baixarBaseDadosMunicipios():
    uri = "geoftp.ibge.gov.br"
    ftp = ftplib.FTP(uri)
    ftp.login("anonymous", "anonymous")
    local = '/organizacao_do_territorio/redes_e_fluxos_geograficos/gestao_do_territorio/bases_de_dados/xls/'
    ftp.cwd(local) 
    arquivo = "ibge/Base_de_dados_dos_municipios.xls"
    arquivoFTP = "Base_de_dados_dos_municipios.xls"
    print('Baixando: ftp://'+uri+local+arquivoFTP)
    ftp.retrbinary("RETR " + arquivoFTP ,open(arquivo, 'wb').write)
    ftp.quit()

def baixarMalhasTerritoriais():
    uri = "geoftp.ibge.gov.br"
    ftp = ftplib.FTP(uri)
    ftp.login("anonymous", "anonymous")
    data = []
    ftp.cwd('/organizacao_do_territorio/malhas_territoriais/malhas_municipais/') 
    ftp.dir("",data.append)
    data = [x.split()[-1] for x in data if x.startswith("d")]
    local = '/organizacao_do_territorio/malhas_territoriais/malhas_municipais/'+data[-1]+'/Brasil/BR/'
    ftp.cwd(local) 
    diretorio = 'ibge'
    if os.path.exists(diretorio):
        shutil.rmtree(diretorio)
    os.makedirs(diretorio)
    arquivo = "ibge/br_municipios.zip"
    arquivoFTP = "br_municipios.zip"
    print('Baixando: ftp://'+uri+local+arquivoFTP)
    ftp.retrbinary("RETR " + arquivoFTP ,open(arquivo, 'wb').write)
    ftp.quit()
    print("Descompactando...")
    with zipfile.ZipFile(arquivo,"r") as zip_ref:
        zip_ref.extractall(diretorio)
    os.remove(arquivo) 
    

def baixarMonitorSecas():
    diretorio = 'ana'
    if os.path.exists(diretorio):
        shutil.rmtree(diretorio)
    os.makedirs(diretorio)
    for a in range((datetime.datetime.now()).year,2013,-1):
        for m in range(1,13,1):
            url = "http://apil5.funceme.br/rest/cms-msne/mapa-monitor?mes="+str(m)+"&ano="+str(a)+"&with=shape&limit=1&orderBy=id,desc"
            page = requests.get(url)
            shape = json.loads(page.content)
            #print(str(shape))
            if(len(shape['data']['list'])>0 and len(shape['data']['list'][0]['shape'])>0):
                urlShape = 'http://f3.funceme.br:9000/msne/'+shape['data']['list'][0]['shape'][0]['path']
                r = requests.get(urlShape, allow_redirects=True)
                arquivo = 'ana/'+str(a)+'_'+str(m).rjust(2, '0')+'.zip'
                open(arquivo, 'wb').write(r.content)
                diretorio2 = 'ana/'+str(a)
                print('Baixando: '+urlShape)
                if not os.path.exists(diretorio2):
                    os.makedirs(diretorio2)
                with zipfile.ZipFile(arquivo,"r") as zip_ref:
                    zip_ref.extractall(diretorio2)
                print('Descompactando: '+arquivo)
                os.remove(arquivo) 
         
def listaShapes():
    shapes = list()
    for path, subdirs, files in os.walk('ana'):
        for name in files:
            nomeCompleto = os.path.join(path, name)
            busca = re.match(r'ana\/[0-9]+\/[a-z]+[0-9]+\/[a-z]+[0-9]+\.shp', nomeCompleto, re.M|re.I)
            if busca is not None:
                #print(nomeCompleto)
                shapes.append(nomeCompleto)
    return shapes

print('Baixando os shapes dos municipios...')
#baixarMalhasTerritoriais()
print('Baixando a planilha dos municipios...')
#baixarBaseDadosMunicipios()
print('Baixando os shapes do monitor de secas...')
baixarMonitorSecas()

print('Gerando os CSVs...')
for shapeMesAno in listaShapes():
    busca = re.search(r'([a-z]+)[0-9]+\.shp', shapeMesAno, re.M|re.I)
    mes = busca.group(1)
    convert = {"janeiro": '01',"fevereiro": '02',"marco": '03',"abril": '04',"maio": '05',"junho": '06',"julho": '07',"agosto": '08',"setembro": '09',"outubro": '10',"novembro": '11',"dezembro": '12'}
    mes = convert[mes]
    busca = re.search(r'\/([0-9]+)\/', shapeMesAno, re.M|re.I)
    ano = busca.group(1)
    print('Ano: '+ano+' Mes: '+mes )
    #if ano == '2018' and mes == '11':
    municipiosSECA = shapeIntersects(shapeMesAno,'ibge/BRMUE250GC_SIR.shp','ibge/Base_de_dados_dos_municipios.xls')
    salvaArquivo(municipiosSECA,ano,mes)