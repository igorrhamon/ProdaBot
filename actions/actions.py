from rasa_sdk.events import SlotSet, ReminderScheduled, ConversationPaused, ConversationResumed, FollowupAction, Restarted, ReminderScheduled
from typing import Text, List, Dict, Any
import json
import os
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
from rasa_sdk.types import DomainDict
from pyotrs import Client, Ticket, Article


from pyotrs import Client
from pyotrs import Article, Client, DynamicField, Ticket
from ldap3 import Server, Connection, ALL, NTLM, ALL_ATTRIBUTES

def criar_artigo_impressora_acesso(artigo,body):
        server_uri = r"http://172.20.101.163/otrs/nph-genericinterface.pl/Webservice/1"
        client = Client(server_uri, "root@localhost", "byrEbIuYpK0lQots")
        #client = Client(server_uri, "otrs", "rogirh17")
        #client.session_restore_or_create()
        client.session_create()


        #body = "Solicitado o acesso à impressora "+str(artigo.get("EndLog"))
        new_ticket = Ticket.create_basic(artigo.get("Title"),Queue="Raw",State=u"new",Priority=u"3 normal",CustomerUser=artigo.get("CustomerUser"))
        first_article = Article({"Acesso Impressora": "Subj", "Body": body,"MimeType": "text/html"})
        client.ticket_create(new_ticket, first_article)
        return new_ticket.to_dct()

def criar_body_auto_ticket(entries_solicitante, entries_l, end_log):
    b = "<h1>Autorização de acesso a sistemas</h1><h2>Dados do solicitante:</h2><ul><li><b>Nome:</b><span>{}</span></li><li><b>Situação:</b><span>ATIVO</span></li><li><b>Login:</b><span>{}</span></li><li><b>Sit. Login:</b><span>Ativo</span></li><li><b>Tipo: </b><span>{}</span></li><li><b>Cargo:</b><span><li><b>Cargo:</b><span>{}</span></li><li><b>Órgão de lotação:</b><span>{}</span></li></ul><h2>Escolha as pessoas para as quais o acesso será concedido/revogado:</h2><ul><li><b>Nome:</b><span>{}</span></li><li><b>Situação:</b><span>ATIVO</span></li><li><b>Login:</b><span>{}</span></li><li><b>Sit. Login:</b><span>Ativo</span></li><li><b>Tipo: </b><span>{}</span></li><li><b>Cargo:</b><span>{}</span></li><li><b>Órgão de lotação:</b><span>{}</span></li></ul><h2>Dados da solicitação:</h2><p><b>Sistemas/perfis de acesso a conceder:</b><br /><pre>Solicito acesso remoto a estação de trabalho {}.</pre></p>".format(entries_solicitante.displayName,entries_solicitante.mailNickname,entries_solicitante.extensionAttribute12,entries_solicitante.extensionAttribute12,entries_solicitante.department,entries_l.displayName,entries_l.mailNickname,entries_l.extensionAttribute12,entries_l.extensionAttribute12,entries_l.department,end_log)
    return b

def procura_login(login):
    server = Server('senado.gov.br', get_info=ALL)
    conn = Connection(server, user=os.environ['senadoUser'], password=os.environ['senadoPassword'], authentication=NTLM)
    conn.bind()
    conn.search('dc=senado,dc=gov,dc=br', '(sAMAccountName={})'.format( login), attributes=ALL_ATTRIBUTES)
    entry = conn.entries[0]
    return entry


class validate_FormInfo(FormValidationAction):
    def name(self) -> Text:
        return "validate_form_info"


    def validate_login_solicitante(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate cuisine value."""   
        server = Server('senado.gov.br', get_info=ALL)
        conn = Connection(server, user=os.environ['senadoUser'], password=os.environ['senadoPassword'], authentication=NTLM)
        conn.bind()
        #fc2 = False
        #loginvalidado = False
        #conn.search('dc=senado,dc=gov,dc=br', '(sAMAccountName~={})'.format( slot_value.lower()), attributes="userPrincipalName")
        try:
            conn.search('dc=senado,dc=gov,dc=br', '(sAMAccountName={})'.format( slot_value.lower()), attributes=ALL_ATTRIBUTES)
            entry = conn.entries
            
            #Checar se tem cargo FC 2
            entry_json = entry[0].entry_to_json()
            
            entry_Json_Load = json.loads(entry_json)
            conn.unbind()
            #print (jsonTeste)
            #print (entry_Json_Load['attributes']['extensionAttribute14'][0])
            if 'extensionAttribute14' in entry_Json_Load['attributes']:
                return {"login_solicitante": slot_value}
            else:
                dispatcher.utter_message(template="utter_login_nao_fc2")
                return {"login_solicitante": None}
        except:
            dispatcher.utter_message(text="Login inválido")
            return {"login_solicitante": None}

            
    def validate_end_log(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate cuisine value."""
        server = Server('senado.gov.br', get_info=ALL)
        conn = Connection(server, user=os.environ['senadoUser'], password=os.environ['senadoPassword'], authentication=NTLM)
        conn.bind()
        #conn.search('dc=senado,dc=gov,dc=br', '(&(printerName={})'.format( slot_value.lower()), attributes=[ 'printerName'])
        end_log_verificado = False

        try:
            conn.search('dc=senado,dc=gov,dc=br', '(printShareName={})'.format( slot_value.lower()), attributes=[ 'printShareName'])
            entry = conn.entries[0]
            try:
                for i in entry.printShareName:
                    end_log_verificado = True
            except: 
                end_log_verificado = False
        finally:
            if end_log_verificado:
                # validation succeeded, set the value of the "cuisine" slot to value
                #dispatcher.utter_message(text="Endereço Lógico validado")
                dispatcher.utter_message(text="Endereço Lógico validado")
                return {"end_log": slot_value}
            else:
                # validation failed, set this slot to None so that the
                # user will be asked for the slot again
                dispatcher.utter_message(text="Endereço Lógico invalido")
                return {"end_log": None}

    def validate_login_l(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate cuisine value."""
        server = Server('senado.gov.br', get_info=ALL)
        conn = Connection(server, user=os.environ['senadoUser'], password=os.environ['senadoPassword'], authentication=NTLM)
        conn.bind()

        login_l= "igorrc"
        login_solicitante = "rabelo"

        try:
            conn.search('dc=senado,dc=gov,dc=br', '(sAMAccountName={})'.format( login_l), attributes=ALL_ATTRIBUTES)
            #Procura o login do autorizado
        except:
            print ("Login incorreto")
            dispatcher.utter_message(text="Login incorreto")
            return {"login_l": None}
        finally:
            entries_l = conn.entries[0]

            conn.search('dc=senado,dc=gov,dc=br', '(sAMAccountName={})'.format( login_solicitante), attributes=ALL_ATTRIBUTES)

            entries_solicitante = conn.entries[0]
            #Exibe cada um
            #Exibe um atributo entry.nomeDoAtt
            funcionarios = list (entries_solicitante.directReports.values)
            e_chefe = False
            for f in funcionarios:
                if entries_l.distinguishedName == f:
                    print ("Verifiquei que você é chefe do setor do {}, vou abrir chamado".format(entries_l.sAMAccountName))
                    dispatcher.utter_message(text="O {} é do seu setor. Vou abrir chamado".format(entries_l.givenName))
                    e_chefe = True
            conn.unbind()
            if (e_chefe)== False:
                print ("Você não faz parte do setor do {}".format(entries_l.givenName))
                dispatcher.utter_message(text="Você não faz parte do setor do {}".format(entries_l.givenName))
                return {"login_l": None}
            else:
                return {"login_l": slot_value}
    
    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        required_slots = ["login_solicitante", "end_log", "login_l"]
        

        for slot_name in required_slots:
            if tracker.slots.get(slot_name) is None:
                # The slot is not filled yet. Request the user to fill this slot next.
                return [SlotSet("requested_slot", slot_name)]

        # All slots are filled.
        numero = 0
        end_log = tracker.get_slot('end_log')
        artigo = {"Title":"Acesso a impressora {}".format(end_log),"CustomerUser":"root@localhost","EndLog":end_log}
        login_solicitante = procura_login(tracker.get_slot('login_solicitante'))
        login_l = procura_login(tracker.get_slot('login_l'))
        body = criar_body_auto_ticket(login_solicitante,login_l,end_log)
        x = criar_artigo_impressora_acesso(artigo,body)
        numero = x.get('TicketNumber')
        #tracker.set_slot("num_chamado", numero)
        return [SlotSet("requested_slot", None), SlotSet("num_chamado", numero)]


    
