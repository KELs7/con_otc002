import unittest

from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        with open("basic-token.py") as f:
            code = f.read()
            self.c.submit(code, name="currency", constructor_args={"vk": "sys"})
            self.c.submit(code, name="con_rswp_lst001", constructor_args={"vk": "sys"}) 
            self.c.submit(code, name="con_marmite100_contract", constructor_args={"vk": "sys"})  
            self.c.submit(code, name="con_unsupported_token", constructor_args={"vk": "sys"})

        self.currency = self.c.get_contract("currency")
        self.rswp = self.c.get_contract("con_rswp_lst001")
        self.marmite = self.c.get_contract("con_marmite100_contract")
        self.unsupported_token = self.c.get_contract("con_unsupported_token")

        with open("../con_otc002.py") as f:
            code = f.read()
            self.c.submit(code, name="con_otc002")

        self.otc = self.c.get_contract("con_otc002")

        
        
        self.setupToken()

    def setupToken(self):
        # Approvals
        self.rswp.approve(signer='endo', amount=999999999, to='con_otc002')
        self.rswp.approve(signer='marvin', amount=999999999, to='con_otc002')
        self.marmite.approve(signer='endo', amount=999999999, to='con_otc002')
        self.marmite.approve(signer='marvin', amount=999999999, to='con_otc002')
        
    def tearDown(self):
        self.c.flush()

    def test_01_usual_otcing_should_pass(self):
        #assign balances
        self.rswp.balances['endo'] = 1000
        self.rswp.balances['marvin'] = 7500
        self.marmite.balances['endo'] = 1000
        self.marmite.balances['marvin'] = 7500

        offer_amount = 50
        take_amount = 2000
        fee = ContractingDecimal('0.7')
        
        offer_id = self.otc.make_offer(signer='endo', offer_token="con_rswp_lst001", \
            offer_amount=offer_amount, take_token="con_marmite100_contract",take_amount=take_amount)

        self.otc.take_offer(signer='marvin', offer_id=offer_id)

        maker_fee = offer_amount / 100 * fee
        taker_fee = take_amount / 100 * fee
        maker_balance_rswp = 1000 - (offer_amount + maker_fee)
        maker_balance_marmite = 1000 + take_amount
        taker_balance_rswp = 7500 + offer_amount
        taker_balance_marmite = 7500 - (take_amount + taker_fee)

        #print(self.rswp.balances['endo'])

        self.assertEqual(maker_balance_rswp, self.rswp.balances['endo'])
        self.assertEqual(maker_balance_marmite, self.marmite.balances['endo'])
        self.assertEqual(taker_balance_rswp, self.rswp.balances['marvin'])
        self.assertEqual(taker_balance_marmite, self.marmite.balances['marvin'])

    def test_02_otcing_unsupported_token_should_fail(self):
        offer_amount = 50
        take_amount = 2000

        with self.assertRaises(AssertionError):
            self.otc.make_offer(signer='endo', offer_token="con_spooky_lst001", \
                offer_amount=offer_amount, take_token="con_marmite100_contract",take_amount=take_amount)

    def test_03_payout_to_owners_should_pass(self):
        #assign balances
        self.currency.balances["con_otc002"] = 2000
        self.rswp.balances["con_otc002"] = 40_000
        self.marmite.balances["con_otc002"] = 10_000_000

        payout_currency = 1000
        payout_rswp = 20_000
        payout_marmite = 5_000_000

        endo_perc = ContractingDecimal('0.5')
        marvin_perc = ContractingDecimal('0.5')

        token_list = ["currency", "con_rswp_lst001", "con_marmite100_contract"]

        self.otc.payout_owners(signer="endo", token_list=token_list)
        
        endo_balance_currency = payout_currency * endo_perc
        endo_balance_rswp = payout_rswp * endo_perc
        endo_balance_marmite = payout_marmite * endo_perc

        marvin_balance_currency = payout_currency * marvin_perc
        marvin_balance_rswp = payout_rswp * marvin_perc
        marvin_balance_marmite = payout_marmite * marvin_perc

        self.assertEqual(endo_balance_currency, self.currency.balances['endo'])
        self.assertEqual(endo_balance_rswp, self.rswp.balances['endo'])
        self.assertEqual(endo_balance_marmite, self.marmite.balances['endo'])
        self.assertEqual(marvin_balance_currency, self.currency.balances['marvin'])
        self.assertEqual(marvin_balance_rswp, self.rswp.balances['marvin'])
        self.assertEqual(marvin_balance_marmite, self.marmite.balances['marvin'])

    
    
    def test_04_adding_token_support_should_pass(self):
        
        new_token_list = self.otc.support_token(signer='marvin', contract="con_spooky_lst001")
        
        supported_tokens = [
            'currency','con_rswp_lst001',
            'con_weth_lst001', 'con_lusd_lst001',
            'con_reflecttau_v2', 'con_marmite100_contract',
            'con_spooky_lst001'
        ]

        self.assertEqual(supported_tokens, new_token_list)

    def test_05_removing_token_support_should_pass(self):
        
        new_token_list = self.otc.remove_token_support(signer='marvin', contract="con_marmite100_contract")
        
        supported_tokens = [
            'currency','con_rswp_lst001',
            'con_weth_lst001', 'con_lusd_lst001',
            'con_reflecttau_v2', 
        ]

        self.assertEqual(supported_tokens, new_token_list)
    
if __name__ == "__main__":
    unittest.main()


