# from odoo import models, fields
#
# # You can store multiple historical agreements per case but only one “active”.
# class LawFeeAgreement(models.Model):
#     _name = 'law.fee.agreement'
#     _description = 'Fee Agreement'
#
#     case_id = fields.Many2one('law.case', required=True)
#     type = fields.Selection([...], required=True)
#     hourly_rate = fields.Monetary()
#     flat_fee_amount = fields.Monetary()
#     contingency_percentage = fields.Float()
#     retainer_amount = fields.Monetary()
#     signed_date = fields.Date()
#     signed_by_id = fields.Many2one('res.partner', string="Signed By (Client)")