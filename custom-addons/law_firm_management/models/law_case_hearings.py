# from odoo import models, fields
#
# class LawCaseHearing(models.Model):
#     _name = 'law.case.hearing'
#     _description = 'Case Hearing / Court Session'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     name = fields.Char(string="Title", required=True)
#     case_id = fields.Many2one('law.case', required=True, ondelete='cascade')
#     court_name = fields.Char()
#     judge_id = fields.Many2one('res.partner', domain=[('is_company', '=', False)])
#     date_start = fields.Datetime(required=True)
#     date_end = fields.Datetime()
#     location = fields.Char()
#     hearing_type = fields.Selection([
#         ('pretrial', 'Pre-trial'),
#         ('trial', 'Trial'),
#         ('hearing', 'Hearing'),
#         ('mediation', 'Mediation'),
#         ('other', 'Other'),
#     ], default='hearing')
#
#     result = fields.Selection([
#         ('scheduled', 'Scheduled'),
#         ('held', 'Held'),
#         ('postponed', 'Postponed'),
#         ('canceled', 'Canceled'),
#     ], default='scheduled')
#     notes = fields.Text()
#
#     calendar_event_id = fields.Many2one('calendar.event', string="Calendar Event")