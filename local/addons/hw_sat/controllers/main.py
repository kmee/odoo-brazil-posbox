# -*- coding: utf-8 -*-
import openerp.addons.hw_proxy.controllers.main as hw_proxy
from openerp import http
from .sat import Sat
from mfecfe.clientelocal import ClienteSATLocal


class SatDriver(hw_proxy.Proxy):

    def get_status(self):
        statuses = {}
        for driver in hw_proxy.drivers:
            if not isinstance(hw_proxy.drivers[driver].device, ClienteSATLocal):
                statuses[driver] = hw_proxy.drivers[driver].get_status()
            else:
                statuses[driver] = {'status': 'connected', 'messages': ['Connected to SAT']}
        return statuses

    # TODO: Temos um problema quando o sat é iniciado depois do POS
    # @http.route('/hw_proxy/status_json', type='json', auth='none', cors='*')
    # def status_json(self):
    #     if not hw_proxy.drivers['satcfe'].device:
    #         hw_proxy.drivers['satcfe'].get_device()
    #     return self.get_status()

    @http.route('/hw_proxy/enviar_pagamento/', type='json', auth='none', cors='*')
    def enviar_pagamento(self, json):
        numero_caixa = json['configs_sat']['numero_caixa']
        cnpjsh = '98155757000159' # json['configs_sat']['cnpj_software_house']
        icms_base = json['orderlines'][0]['estimated_taxes']
        valor_total_venda = json['orderlines'][0]['price_with_tax']
        multiplos_pagamentos = True
        controle_antifraude = False
        codigo_moeda = json['currency']['name']
        cupom_nfce = True

        resposta = hw_proxy.drivers['mfesat'].enviar_pagamento('26359854-5698-1365-9856-965478231456', numero_caixa,'TEF',
        '30146465000116', icms_base, valor_total_venda, multiplos_pagamentos, controle_antifraude, codigo_moeda, cupom_nfce, 'False')

        resposta_pagamento = resposta.split('|')

        if len(resposta_pagamento[0]) >= 7:
            self.id_pagamento = resposta_pagamento[0]
            self.id_fila = '958860'
            self.numero_identificador = resposta_pagamento[1]

            # Retorno do status do pagamento só é necessário em uma venda
            # efetuada por TEF.
            # TODO: fazer uma rotina para verificar ate o pagamento ser confirmado
            resposta_pagamento_validador = hw_proxy.drivers['mfesat'].verificar_status_validador(
                cnpjsh, self.id_fila
            )

            resposta_dados_venda = hw_proxy.drivers['mfesat'].\
                enviar_dados_venda(resposta_pagamento_validador,
                                   self.numero_identificador)

            resposta_dados_venda

            self.pagamento_valido = True

        return True

    @http.route('/hw_proxy/init/', type='json', auth='none', cors='*')
    def init(self, json):
        hw_proxy.drivers['satcfe'] = Sat(**json)
        return True

    # @http.route('/hw_proxy/init_mfe/', type='json', auth='none', cors='*')
    # def init_mfe(self, json):
    #     hw_proxy.drivers['mfesat'] = ClienteVfpeLocal(BibliotecaMFE('/home/atillasilva/Integrador'),
    #                                                   chave_acesso_validador='25CFE38D-3B92-46C0-91CA-CFF751A82D3D')
    #     return True

    @http.route('/hw_proxy/enviar_cfe_sat/', type='json', auth='none', cors='*')
    def enviar_cfe_sat(self, json):
        return hw_proxy.drivers['satcfe'].action_call_sat('send', json)

    @http.route('/hw_proxy/cancelar_cfe/', type='json', auth='none', cors='*')
    def cancelar_cfe(self, json):
        return hw_proxy.drivers['satcfe'].action_call_sat('cancel', json)

    @http.route('/hw_proxy/reprint_cfe/', type='json', auth='none', cors='*')
    def reprint_cfe(self, json):
        return hw_proxy.drivers['satcfe'].action_call_sat('reprint', json)
