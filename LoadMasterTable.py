import pandas as pd
from mapping import Base
from mapping import engine


def LoadMasterTable(mapping, info_path, table_name, engine, schema):
    # mapping: sqlalchemy.ext.automap (Base.classes)
    # info_path: string with file path ('MasterTables.xls')
    # table_name: string with table name ('evidence')
    # engine: database conection
    # schema: ('bioacustica')
    columns_names = mapping[table_name].__table__.columns.keys()
    tableToLoad = pd.read_excel(info_path, sheet_name = table_name, header = None)
    tableToLoad = tableToLoad.applymap(lambda x: x.replace('"','').upper())
    tableToLoad.columns = [columns_names[1]]
    tableToLoad[columns_names[0]] = range(1,tableToLoad.shape[0]+1)
    tableToLoad = tableToLoad.reindex(columns = columns_names)
    tableToLoad.to_sql(name = table_name, schema ='bioacustica', index = False, con = engine, if_exists = 'append')



sheets = pd.ExcelFile('MasterTables.xls').sheet_names

for sheet in sheets:
    try:
        LoadMasterTable(mapping = Base.classes,
                        info_path = 'MasterTables.xls',
                        table_name = sheet,
                        engine = engine,
                        schema = 'bioacustica')
    except:
        print("Error",sheet)

#----------------------------------

from mapping import Base
from mapping import engine
from sqlalchemy.orm import Session

session = Session(engine)

session.add(Base.classes["user"](name = "JUAN MANUEL",
                                 email = "juanm.daza@udea.edu.co",
                                 username = "juanm.daza",
                                 roles = "ADMINISTRADOR"))
session.commit()


#----------------------------------

from sqlalchemy.orm import Session

session = Session(engine)

id_funding = session.query(Base.classes["funding"]).filter(Base.classes["funding"].description == 'GHA').first().id_funding
session.add(Base.classes["project"](id_funding = id_funding,
                                    description = "Proyecto Piloto YNC",))
session.commit()


#----------------------------------

import datetime
import pandas as pd
from mapping import Base
from mapping import engine
from sqlalchemy.orm import Session

session = Session(engine)


def SamplingAdd(file, session):
    
    udas = pd.read_excel(file, sheet_name = "UDAS", header = 0)
    
    id_season = session.query(Base.classes["season"]).filter(Base.classes["season"].description == udas.iloc[0]["season_HA"]).first().id_season
    #id_funding = session.query(Base.classes["funding"]).filter(Base.classes["funding"].description == udas.iloc[0]["funding_PR"]).first().id_funding
    id_project = session.query(Base.classes["project"]).filter(Base.classes["project"].description == udas.iloc[0]["project_name_PR"]).first().id_project
    id_cataloger = session.query(Base.classes["user"]).filter(Base.classes["user"].email == udas.iloc[0]["collector_email_PR"]).first().id_user
    
    session.add(Base.classes["sampling"](id_project = id_project,
                                         id_cataloger = id_cataloger,
                                         id_season = id_season,
                                         date = datetime.datetime.now(),
                                         description = udas.iloc[0]["id_DM"]))
    session.commit()



SamplingAdd(file = "../UDAS_20210406.xls", session = session)

#----------------------------------

# Temas a discutir
# 1) Dependencia entre project y funding
# 2) Coherencia entre la información de las tablas maestras y la plantilla (tocaria agregar mas información a las tablas maestras o editarlas?)
# 3) Como referenciar al usuario (por email, nombre o username)
# 4) Hablar de la plantilla (separar por hojas (sampling, catalogo y registro)) es un UDAS por sampling
# 5) nombre del sampling (nombre del estudio) iria en description
