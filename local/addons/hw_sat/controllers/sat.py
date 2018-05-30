# -*- coding: utf-8 -*-
import logging
import time
from threading import Thread, Lock
from requests import ConnectionError
from pybrasil.valor.decimal import Decimal
import StringIO
import base64
import string

from satcfe.entidades import Emitente
from satcfe.entidades import Destinatario
from satcfe.entidades import Detalhamento
from satcfe.entidades import ProdutoServico
from satcfe.entidades import Imposto
from satcfe.entidades import ICMS00
from satcfe.entidades import PISSN
from satcfe.entidades import COFINSSN
from satcfe.entidades import MeioPagamento
from satcfe.entidades import CFeVenda
from satcfe.entidades import InformacoesAdicionais
from satcfe.entidades import CFeCancelamento
from satcfe.excecoes import ErroRespostaSATInvalida
from satcfe.excecoes import ExcecaoRespostaSAT

from satcfe.clientelocal import ClienteSATLocal
from satcfe import BibliotecaSAT

from mfecfe.clientelocal import ClienteSATLocal as ClienteMFELocal
from mfecfe import BibliotecaSAT as BibliotecaMFE

from satextrato import ExtratoCFeCancelamento, ExtratoCFeVenda

_logger = logging.getLogger(__name__)


TWOPLACES = Decimal(10) ** -2
FOURPLACES = Decimal(10) ** -4


def punctuation_rm(string_value):
    tmp_value = string_value.translate(None, string.punctuation)
    return tmp_value


class XPathMap(object):

    def __init__(self, root):
        self.root = root

    def __getitem__(self, key, default=None):
        nodelist = self.root.findtext(key)
        if not nodelist:
            return '*'
        if len(nodelist) > 1:
            return nodelist
        return nodelist[0]


class Sat(Thread):
    def __init__(self, codigo_ativacao, sat_path, impressora, printer_params,
                 assinatura, tipo_equipamento):
        Thread.__init__(self)
        self.codigo_ativacao = codigo_ativacao
        self.sat_path = sat_path
        self.impressora = impressora
        self.printer_params = printer_params
        self.lock = Lock()
        self.satlock = Lock()
        self.status = {'status': 'connecting', 'messages': []}
        self.printer = False
        self.tipo_equipamento = tipo_equipamento
        self.device = self._get_device()
        self.assinatura = assinatura


    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.daemon = True
                self.start()

    def get_status(self):
        self.lockedstart()
        return self.status

    def set_status(self, status, message=None):
        if status == self.status['status']:
            if message is not None and message != self.status['messages'][-1]:
                self.status['messages'].append(message)

                if status == 'error' and message:
                    _logger.error('SAT Error: '+message)
                elif status == 'disconnected' and message:
                    _logger.warning('Disconnected SAT: '+message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

            if status == 'error' and message:
                _logger.error('SAT Error: '+message)
            elif status == 'disconnected' and message:
                _logger.warning('Disconnected SAT: '+message)

    def _get_device(self):
        if not self.sat_path and not self.codigo_ativacao:
            self.set_status('error', 'Dados do sat incorretos')
            return None
        if self.tipo_equipamento == 'mfe':
            return ClienteMFELocal(
                BibliotecaMFE(self.sat_path),
                codigo_ativacao=self.codigo_ativacao
            )
        return ClienteSATLocal(
            BibliotecaSAT(self.sat_path),
            codigo_ativacao=self.codigo_ativacao
        )

    def status_sat(self):
        with self.satlock:
            if self.device:
                try:
                    consulta = self.device.consultar_sat()
                    if consulta:
                        self.set_status('connected', 'Connected to SAT')
                except ErroRespostaSATInvalida as ex_sat_invalida:
                    # o equipamento retornou uma resposta que não faz sentido;
                    # loga, e lança novamente ou lida de alguma maneira
                    self.device = None
                except ExcecaoRespostaSAT as ex_resposta:
                    self.set_status('disconnected', 'SAT Not Found')
                    self.device = None
                except ConnectionError as ex_conn_error:
                    self.device = None
                except Exception as ex:
                    self.set_status('error', str(ex))
                    self.device = None

    def __prepare_send_detail_cfe(self, item):
        kwargs = {}

        if item['discount']:
            kwargs['vDesc'] = Decimal((item['quantity'] * item['price']) -
                                      item['price_display']).quantize(TWOPLACES)
        estimated_taxes = Decimal(item['estimated_taxes'] * item['price_display']).quantize(TWOPLACES)

        detalhe = Detalhamento(
            produto=ProdutoServico(
                cProd=unicode(item['product_default_code']),
                xProd=item['product_name'],
                CFOP='5102',
                uCom=item['unit_name'],
                qCom=Decimal(item['quantity']).quantize(FOURPLACES),
                vUnCom=Decimal(item['price']).quantize(TWOPLACES),
                indRegra='A',
                NCM=punctuation_rm(item['fiscal_classification_id'][1]),
                **kwargs
                ),
            imposto=Imposto(
                vItem12741=estimated_taxes,
                icms=ICMS00(Orig=item['origin'], CST='00', pICMS=Decimal('18.00')),
                pis=PISSN(CST='49'),
                cofins=COFINSSN(CST='49'))
        )
        detalhe.validar()
        return detalhe, estimated_taxes

    def __prepare_payment(self, json):
        kwargs = {}
        if json['sat_card_accrediting']:
            kwargs['cAdmC'] = json['sat_card_accrediting']

        pagamento = MeioPagamento(
            cMP=json['sat_payment_mode'],
            vMP=Decimal(json['amount']).quantize(
                TWOPLACES),
            **kwargs
        )
        pagamento.validar()
        return pagamento

    def __prepare_send_cfe(self, json):
        detalhamentos = []
        total_taxes = Decimal(0)
        for item in json['orderlines']:
            detalhe, estimated_taxes = self.__prepare_send_detail_cfe(item)
            detalhamentos.append(detalhe)
            total_taxes += estimated_taxes

        # descontos_acrescimos_subtotal = DescAcrEntr(
        #     vCFeLei12741=total_taxes)
        # descontos_acrescimos_subtotal.validar()

        pagamentos = []
        for pagamento in json['paymentlines']:
            pagamentos.append(self.__prepare_payment(pagamento))

        kwargs = {}
        if json['client']:
            # TODO: Verificar se tamanho == 14: cnpj
            kwargs['destinatario'] = Destinatario(CPF=json['client'])
        emitente = Emitente(
                CNPJ=u'08723218000186',
                IE=u'562377111111',
                indRatISSQN='N')
        emitente.validar()

        informacoes_adicionais = json.get('informacoes_adicionais')
        if informacoes_adicionais is not None:
            kwargs['informacoes_adicionais'] = InformacoesAdicionais(
                # informacoes_adicionais pode ser um inteiro ou unicode:
                infCpl=u"%s" % (informacoes_adicionais,),
            )

        return CFeVenda(
            CNPJ=u'16716114000172',
            signAC=u'SGR-SAT SISTEMA DE GESTAO E RETAGUARDA DO SAT',
            numeroCaixa=json['configs_sat']['numero_caixa'],
            emitente=emitente,
            detalhamentos=detalhamentos,
            pagamentos=pagamentos,
            vCFeLei12741=total_taxes,
            **kwargs
        )

    def _send_cfe(self, json):
        try:
            dados = self.__prepare_send_cfe(json)
            resposta = self.device.enviar_dados_venda(dados)
            # self._print_extrato_venda(resposta.arquivoCFeSAT)
            print (resposta)
            return {
                'xml': resposta.arquivoCFeSAT,
                'numSessao': resposta.numeroSessao,
                'chave_cfe': resposta.chaveConsulta,
            }
        except Exception as e:
            if hasattr(e, 'resposta'):
                return e.resposta.mensagem
            elif hasattr(e, 'message'):
                return e.message
            else:
                return "Erro ao validar os dados para o xml! " \
                       "Contate o suporte técnico."

    def __prepare_cancel_cfe(self, chCanc, cnpj):
        kwargs = {}

        return CFeCancelamento(
            chCanc=chCanc,
            CNPJ=punctuation_rm(cnpj),
            signAC=self.assinatura,
            numeroCaixa=2,
            **kwargs
        )

    def _cancel_cfe(self, order):
        try:
            resposta = self.device.cancelar_ultima_venda(
                order['chaveConsulta'],
                self.__prepare_cancel_cfe(
                    order['chaveConsulta'], order['cnpj_software_house']
                )
            )
            # self._print_extrato_cancelamento(
            #     order['xml_cfe_venda'], resposta.arquivoCFeBase64)
            return {
                'order_id': order['order_id'],
                'xml': resposta.arquivoCFeBase64,
                'numSessao': resposta.numeroSessao,
                'chave_cfe': resposta.chaveConsulta,
            }
        except Exception as e:
            _logger.error('_cancel_cfe', exc_info=1)
            if hasattr(e, 'resposta'):
                return e.resposta.mensagem
            elif hasattr(e, 'message'):
                return e.message
            else:
                return "Erro ao validar os dados para o xml! " \
                       "Contate o suporte técnico."

    def action_call_sat(self, task, json=False):

        _logger.info('SAT: Task {0}'.format(task))

        try:
            with self.satlock:
                if task == 'connect':
                    pass
                elif task == 'get_device':
                    return self._get_device()
                elif task == 'reprint':
                    return self._reprint_cfe(json)
                elif task == 'send':
                    return self._send_cfe(json)
                elif task == 'cancel':
                    return self._cancel_cfe(json)
        except ErroRespostaSATInvalida as ex:
            _logger.error('SAT Error: {0}'.format(ex))
            return {'excessao': ex}
        except ExcecaoRespostaSAT as ex:
            _logger.error('SAT Error: {0}'.format(ex))
            return {'excessao': ex}
        except Exception as ex:
            _logger.error('SAT Error: {0}'.format(ex))
            return {'excessao': ex}

    def _init_printer(self):

        # from escpos.serial import SerialSettings
        #
        # if self.impressora == 'epson-tm-t20':
        #     _logger.info(u'SAT Impressao: Epson TM-T20')
        #     from escpos.impl.epson import TMT20 as Printer
        # elif self.impressora == 'bematech-mp4200th':
        #     _logger.info(u'SAT Impressao: Bematech MP4200TH')
        #     from escpos.impl.bematech import MP4200TH as Printer
        # elif self.impressora == 'daruma-dr700':
        #     _logger.info(u'SAT Impressao: Daruma Dr700')
        #     from escpos.impl.daruma import DR700 as Printer
        # elif self.impressora == 'elgin-i9':
        #     _logger.info(u'SAT Impressao: Elgin I9')
        #     from escpos.impl.elgin import ElginI9 as Printer
        # else:
        #     self.printer = False
        # conn = SerialSettings.as_from(
        #     self.printer_params).get_connection()

        return impressora_elgin

    def _print_extrato_venda(self, xml):
        if not self.printer:
            return False
        extrato = ExtratoCFeVenda(
            StringIO.StringIO(base64.b64decode(xml)),
            self.printer
            )
        anotacoes_corpo = '\n'.join([
            '{xml[infCFe/infAdic/infCpl]}',
            'Venda no.: {xml[infCFe/ide/nserieSAT]} / {xml[infCFe/ide/nCFe]}',
        ]).format(
            xml=XPathMap(extrato.root),
        ).splitlines()
        extrato.anotacoes_corpo.extend(anotacoes_corpo)
        extrato.imprimir()
        return True

    def _print_extrato_cancelamento(self, xml_venda, xml_cancelamento):
        if not self.printer:
            return False
        extrato = ExtratoCFeCancelamento(
            StringIO.StringIO(base64.b64decode(xml_venda)),
            StringIO.StringIO(base64.b64decode(xml_cancelamento)),
            self.printer
            )
        extrato.imprimir()
        return True

    def _reprint_cfe(self, json):
        if json['canceled_order']:
            return self._print_extrato_cancelamento(
                json['xml_cfe_venda'], json['xml_cfe_cacelada'])
        else:
            return self._print_extrato_venda( json['xml_cfe_venda'])

    def run(self):
        self.device = None
        while True:
            if self.device:
                self.status_sat()
                time.sleep(40)
            else:
                self.device = self.action_call_sat('get_device')
                if not self.device:
                    time.sleep(40)
