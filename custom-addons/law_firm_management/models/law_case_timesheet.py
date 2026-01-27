# from odoo import models, fields
#
# class LawCaseTimesheet(models.Model):
#     _name = 'law.case.timesheet'
#     _description = 'Case Timesheet Entry'
#     _inherit = ['mail.thread']
#
#     case_id = fields.Many2one('law.case', required=True, ondelete='cascade')
#     lawyer_id = fields.Many2one('res.partner', domain=[('is_lawyer', '=', True)], required=True)
#     user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
#     date = fields.Datetime(default=fields.Datetime.now, required=True)
#     duration_hours = fields.Float(required=True)
#     description = fields.Text()
#     is_billable = fields.Boolean(default=True)
#
#     hourly_rate = fields.Monetary()
#     amount = fields.Monetary(compute="_compute_amount", store=True)
#     currency_id = fields.Many2one('res.currency', related='case_id.currency_id', store=True)
#
#     invoice_line_id = fields.Many2one('account.move.line')
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('to_invoice', 'To Invoice'),
#         ('invoiced', 'Invoiced'),
#         ('non_billable', 'Non-billable'),
#     ], default='draft')
#
#     @api.depends('duration_hours', 'hourly_rate')
#     def _compute_amount(self):
#         for rec in self:
#             rec.amount = rec.duration_hours * (rec.hourly_rate or 0.0)
#
# # On create / write you can default hourly_rate from:
# # 1. case’shourly_rate
# # 2.lawyer’sdefault_hourly_rate
# # 3.global default