import requests
from wikibaseintegrator import wbi_core, wbi_login, wbi_datatype

#Logging in with Wikibase Integrator
print("Logging in with Wikibase Integrator")
login_instance = wbi_login.Login(user="OpenCitations Bot", pwd="ocbot123")


#Opening the list of Wikidata items with DOI
file = open("wikidata_doi.tsv", "r")

#Setting COCI as a reference for the created statements
wid1 = ""
source = [
          [
            wbi_datatype.ItemID(value="Q107507940", prop_nr="P248", is_reference=True, if_exists="APPEND")
          ]
         ]


for line in file:
      #Extracting the Wikidata ID and DOI of every single publication from the list of Wikidata items with DOI
      line_elements = line.split("\t")
      wid = line_elements[0]
      doi = line_elements[1][1:-2]

      #Getting the DOIs of the references for every scholarly article
      r = requests.get('https://opencitations.net/index/api/v1/references/'+doi)
      r_data = r.text
      ref_dois = []
      while (r_data.find('"cited": "coci => ') >= 0):
          r_data = r_data[r_data.find('"cited": "coci => ')+18:]
          ref_dois.append(r_data[0:r_data.find('"')])

      #Retrieving Wikidata ID for every DOI
      statements = []
      for i in ref_dois:
          idurl = "https://hub.toolforge.org/P356:"+i+"?format=json"
          idget = requests.get(idurl)
          idjson = idget.json()
          try:
              wid1 = idjson["origin"]["qid"]
          except KeyError:
              wid1 = ""
          #Identifying the missing cites work relations in Wikidata
          if (wid1 != ""):
              statement = wbi_datatype.ItemID(value=wid1, prop_nr="P2860", references=source, if_exists="APPEND")
              statements.append(statement)
          else:
              new_item_statements = []
              #Getting the metadata of the reference publication to be added to Wikidata
              r1 = requests.get("https://opencitations.net/index/api/v1/metadata/"+i)
              #Adding DOI Statements for new items
              doi_r = wbi_datatype.ExternalID(value=i, prop_nr="P356", references=source)
              new_item_statements.append(doi_r)
              r_json = r1.json()           
              for rec in r_json:
                try:
                  n = 0
                  #Adding Authorship Statements for new items
                  author = rec["author"]
                  aut = author.split("; ")
                  for a in aut:
                      n += 1
                      if (a.find(", ")>=0):
                          aus = a.split(", ")
                          str1 = aus[1]+' '+aus[0]
                          strn = str(n)
                          authorqualifier = [
                            wbi_datatype.String(value=strn, prop_nr="P1545", is_qualifier=True)
                            ]
                          author = wbi_datatype.String(value=str1, prop_nr="P2093", qualifiers=authorqualifier, references=source)
                          new_item_statements.append(author)
                      else:
                          authorqualifier = [
                            wbi_datatype.String(value=strn, prop_nr="P1545", is_qualifier=True)
                            ]
                          author = wbi_datatype.String(value=a, prop_nr="P2093", qualifiers=authorqualifier, references=source)
                          new_item_statements.append(author)
                except KeyError:
                  author = ""
                #Adding Publication Years for new items
                try:
                  year = str(rec["year"])
                  if (year != ""):
                    year1 = wbi_datatype.Time(time='+'+year+'-00-00T00:00:00Z', prop_nr="P577", references=source)
                    new_item_statements.append(year1)
                except KeyError:
                  year = ""
                #Extracting the titles for new items
                try:
                  title = str(rec["title"])
                except KeyError:
                  title = ""
                #Adding Source Titles to new items
                try:
                  sourcetitle = str(rec["source_title"])
                  if (sourcetitle != ""):
                    sourcequalifier = [
                      wbi_datatype.String(value=sourcetitle, prop_nr="P1932", is_qualifier=True)
                      ]
                    source1 = wbi_datatype.ItemID(value="Q53569537", prop_nr="P1433", qualifiers=sourcequalifier, references=source)
                    new_item_statements.append(source1)
                except KeyError:
                  sourcetitle = ""
                #Adding Volume Number to new items
                try:
                  volume = str(rec["volume"])
                  if (volume != ""):
                    volume1 = wbi_datatype.String(value=volume, prop_nr="P478", references=source)
                    new_item_statements.append(volume1)
                except KeyError:
                  volume = ""
                #Adding Issue Number to new items
                try:
                  issue = str(rec["issue"])
                  if (issue != ""):
                    issue1 = wbi_datatype.String(value=issue, prop_nr="P433", references=source)
                    new_item_statements.append(issue1)
                except KeyError:
                  issue = ""
                #Adding Page Numbers to new items
                try:
                  page = str(rec["page"])
                  if (page != ""):
                    page1 = wbi_datatype.String(value=page, prop_nr="P304", references=source)
                    new_item_statements.append(page1)
                except KeyError:
                  page = ""
                #Adding Open Access Link Statements to new items
                try:
                  oalink = str(rec["oa_link"])
                  if (oalink != ""):
                    oa = wbi_datatype.Url(value=oalink, prop_nr="P856", references=source)
                    new_item_statements.append(oa)
                except KeyError:
                  oalink = ""

              #Creating new item
              item = wbi_core.ItemEngine(data = new_item_statements)
              if (title != ""): item.set_label(title, lang="en")
              item.set_description("scholarly article", lang="en")
              if (len(new_item_statements)>=2):
                try:
                  item.write(login_instance, edit_summary="Uploaded from OpenCitations COCI API using OpenCitations Bot")
                except Exception:
                  print("New item Not Created")
      if (statements != []):
          #Adding Cites Work Relations to Wikidata
          item = wbi_core.ItemEngine(data = statements, item_id = wid)
          item.write(login_instance, edit_summary="Added from OpenCitations COCI API using OpenCitations Bot")
            
          
  
