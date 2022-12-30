import os
from pysec import xbrl

from django.db import models
from django.conf import settings

DATA_DIR = settings.DATA_DIR

class Index(models.Model):
    
    filename = models.TextField()
    name = models.TextField(blank=True)
    date = models.DateField(null=True)
    cik = models.IntegerField()
    form = models.CharField(max_length=10,blank=True)
    quarter = models.CharField(max_length=6,blank=True)
   
    
    def xbrl_link(self):
        if self.form.startswith('10-K') or self.form.startswith('10-Q'):
            id = self.filename.split('/')[-1][:-4]
            return f"http://www.sec.gov/Archives/edgar/data/{self.cik}/{id.replace('-', '')}/{id}-xbrl.zip"
        return None
        
    def html_link(self):
        return f'http://www.sec.gov/Archives/{self.filename}'

    def index_link(self):
        id = self.filename.split('/')[-1][:-4]
        return f"http://www.sec.gov/Archives/edgar/data/{self.cik}/{id.replace('-', '')}/{id}-index.htm"
        
    def txt(self):
        return self.filename.split('/')[-1]
        
    def localfile(self):
        filename = f'{DATA_DIR}/{self.cik}/{self.txt()[:-4]}/{self.txt()}'
        return filename if os.path.exists(filename) else None
        
    def localpath(self):
        return f'{DATA_DIR}/{self.cik}/{self.txt()[:-4]}/'

    def localcik(self):
        return f'{DATA_DIR}/{self.cik}/'
    


    def html(self):
        filename = self.localfile()
        if not filename: 
            return None
        f = open(filename,'r').read()
        f_lower = f.lower()
        try:
            return f[f_lower.find('<html>'):f_lower.find('</html>')+4]
        except:
            print 'html tag not found'
            return f

    def download(self):
        try: 
            os.mkdir(self.localcik())
        except:
            pass
        try:
            os.mkdir(self.localpath())
        except:
            pass
        os.chdir(self.localpath())

        if not os.path.exists(self.html_link().split('/')[-1]):
            os.system(f'wget {self.html_link()}')
        if self.xbrl_link() and not os.path.exists(
            self.xbrl_link().split('/')[-1]
        ):
            os.system(f'wget {self.xbrl_link()}')
            os.system('unzip *.zip')

    def xbrl_localpath(self):
        try:
            os.chdir(self.localpath())
        except:
            self.download()
        files = os.listdir('.')
        xml = sorted([elem for elem in files if elem.endswith('.xml')],key=len)
        return self.localpath() + xml[0] if len(xml) else None


    def xbrl(self):
        filepath = self.xbrl_localpath()  
        if not filepath:
            print 'no xbrl found. this option is for 10-ks.'
            return None                      
        x = xbrl.XBRL(filepath)
        x.fields['FiscalPeriod'] = x.fields['DocumentFiscalPeriodFocus']
        x.fields['FiscalYear'] = x.fields['DocumentFiscalYearFocus']
        x.fields['DocumentPeriodEndDate'] = x.fields['BalanceSheetDate']
        x.fields['PeriodStartDate'] = x.fields['IncomeStatementPeriodYTD']
        x.fields['SECFilingPage'] = self.index_link()
        x.fields['LinkToXBRLInstance'] = self.xbrl_link() 

        return x
        
    def ticker(self): #get a company's stock ticker from an XML filing
        return filepath.split('-')[0] if (filepath := self.xbrl_localpath()) else None
