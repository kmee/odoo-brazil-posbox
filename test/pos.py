import satcfe
from satcomum import constantes
from satcfe import ClienteSATLocal
from satcfe import ClienteSATHub
from satcfe import BibliotecaSAT
from satcfe.entidades import Emitente
from satcfe.entidades import Destinatario
from satcfe.entidades import LocalEntrega
from satcfe.entidades import Detalhamento
from satcfe.entidades import ProdutoServico
from satcfe.entidades import Imposto
from satcfe.entidades import ICMSSN102
from satcfe.entidades import PISSN
from satcfe.entidades import COFINSSN
from satcfe.entidades import MeioPagamento
from satcfe.entidades import CFeVenda
from satcfe.entidades import CFeCancelamento
from satcfe.excecoes import ErroRespostaSATInvalida
from satcfe.excecoes import ExcecaoRespostaSAT

cliente = ClienteSATLocal(
    BibliotecaSAT('/usr/lib/libbemasat.so'),
    codigo_ativacao='bema1234'
   )
print cliente
resposta = cliente.consultar_sat()
print resposta.mensagem


from escpos.serial import SerialSettings
from escpos.impl.epson import TMT20
from satextrato import ExtratoCFeVenda

conn = SerialSettings.as_from('/dev/ttyS0:115200,8,1,N').get_connection()
impressora = TMT20(conn)
impressora.init()

with open(r'/home/ananias/posbox/test/pos_order_1.xml', 'r') as fp:
    extrato = ExtratoCFeVenda(fp, impressora)
    extrato.imprimir()
