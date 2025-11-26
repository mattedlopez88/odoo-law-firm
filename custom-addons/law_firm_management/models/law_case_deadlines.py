# from odoo import models, fields
#
# class LawCaseDeadline(models.Model):
#     _name = 'law.case.deadline'
#     _description = 'Case Deadline'
#     _inherit = ['mail.activity.mixin']
#
#     name = fields.Char(required=True)
#     case_id = fields.Many2one('law.case', required=True, ondelete='cascade')
#     date_due = fields.Datetime(required=True)
#     date_alert = fields.Datetime()
#     type = fields.Selection([
#         ('filing', 'Filing'),
#         ('hearing', 'Hearing-related'),
#         ('internal', 'Internal'),
#         ('court', 'Court Order'),
#     ], default='filing')
#     responsible_id = fields.Many2one('res.users', string="Responsible")
#     state = fields.Selection([
#         ('open', 'Open'),
#         ('done', 'Done'),
#         ('canceled', 'Canceled'),
#     ], default='open')
#
#     notes = fields.Text()
#
#     # link to mail.activity for reminders