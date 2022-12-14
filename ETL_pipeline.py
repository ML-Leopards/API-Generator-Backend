# Extraction, Transformation and Loading pipeline
from analysis import get_csv
import pandas as pd
from cluster_SQL import splitter,gen_module
import mysql.connector

class ETL:
    def __init__(self):
        self.variables = 0;

    def analysis_module(self,file):
        """
        analysis module is being used
        for getting the csv file after
        analysing the whole log file.

        function called: 
        ------------
            get_csv from analysis.py

        paramenters: 
        ------------
            file object: log file

        returns: 
        ------------
            csv file: derived from the log file using ner model
        """
        file.save('./static/chinook2.log')
        with open('./static/chinook2.log','r') as log_file:
            csv_file = get_csv(log_file)
            # df = pd.read_csv(csv_file)
        csv_file.to_csv('./static/chinook2.csv')
        return csv_file

    def countQueries(self):
        df = pd.read_csv('.\static\mysql.csv', squeeze=False,header=0)
        splits = splitter(df)
        return splits

    def getQueriesSQL(self):
        etl = ETL()
        splits = etl.countQueries()
        for i in splits:
            try:
                final_api= gen_module(i)
                final_api.to_csv(f'./static/final{splits.index(i)}.csv',index=False,header=True)
            except ValueError:
                print('No values')


    def createNameQuery(self):
        df = pd.read_csv('./static/final1.csv')
        queries = df['text']
        names = []
        details=[]
        for i in queries:
            i = i.lower()
            etl = ETL()
            i = etl.removePunct(i)
            if '*' in i:
                i = i.replace('*','All')
            list_of_words = i.split()
            if 'from' in list_of_words:
                list_of_words[list_of_words.index('from')]='From'
            if list_of_words[0] == 'select':
                etl = ETL()
                name,detail = etl.select(list_of_words)
                names.append(name)
                details.append(detail)
        df['name'] = names
        df['detail'] = details
        df.to_csv('./static/final1.csv')
        return df 
                
    def select(self,words):
        select_dict={}
        first = []
        second = []
        third = []
        for i in words[1::]:
            if '.' in i:
                index = words.index(i)
                i=i[i.index('.')+1::]
                words[index] = i
             

        for i in words[1::]:
            if i=='From':
                index = words.index(i)
                break;
            else:
                index = words.index(i)
                first.append(i)
        
        for i in words[index+1::]:
            if i == 'where':
                index = words.index(i)
                break;
            else:
                index = words.index(i)
                second.append(i)
        
        for i in words[index+1::]:
            third.append(i)
        
        select_dict['select'] = first
        select_dict['from'] = second
        select_dict['where'] = third

        name = 'read'
        
        if 'as' in first:
            del first[first.index('as')-1]
            del first[first.index('as')]
        
        if len(first)>1:
            name = name + 'Details' 
        else:
            name = name + first[0].capitalize()
        if len(third)!=0:
            try:
                if third.count('{}')>1:
                    name = name +'By'+ third[third.index('{}')-2].capitalize()
                    a = third[third.index('{}')-2].capitalize()
                    third.remove('{}')
                    for j in range(third.count('{}')):
                        if third[third.index('{}')-2].capitalize()!=a:
                            name = name+'And'+third[third.index('{}')-2].capitalize()
                else:
                    name = name +'By'+ third[third.index('{}')-2].capitalize()
            except ValueError:
                name = name +'By'+ third[third.index('=')-1].capitalize()
        return name,first

    
    def removePunct(self,string):
        punc = "',!()-[];:\,/?@#$%^&*_~"
        for ele in string:
            if ele in punc:
                string = string.replace(ele, "")
        return string

    def dfconcat(self):
        for i in range(4):
            dfs=[]
            try:
                df = pd.read_csv(f'./static/file{i}')
                dfs.append(df)
            except FileNotFoundError:
                print('file not found')
        dataframes = pd.concat(dfs)
        dataframes.to_csv('./static/execute.csv')

    def findQuery(self,query_name,query_info):
        df = pd.read_csv('./static/execute.csv')
        query = df['text'].where(df['name'] == query_name)
        datatype = df['datatype'].where(df['name'] == query_name)
        data = tuple()
        if datatype:
            for i in datatype:
                if i=='int':
                    data.append(int(i))
                elif i=='str' or i=='date':
                    data.append("'"+i+"'")
        if '{}' in query:
            query.format(*data)
        return query

    def executeAPISQL(self,username,password,host_url,database,query_name,port,query_info):
        connect = mysql.connector.connect(
        user=username,
        password=password,
        database=database,
        host=host_url,
        port=port)
        cursor = connect.cursor()
        etl=ETL()
        query = etl.findQuery(query_name,query_info)
        cursor.execute(query)
        cursor.close()
        connect.commit()
        connect.close()