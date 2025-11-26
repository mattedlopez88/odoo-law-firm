# from odoo import models, fields
#
# class LawCaseTask(models.Model):
#     _name = 'law.case.task'
#     _description = 'Case Task'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     name = fields.Char(required=True)
#     case_id = fields.Many2one('law.case', required=True)
#     assigned_to_id = fields.Many2one('res.users')
#     deadline_id = fields.Many2one('law.case.deadline', string="Linked Deadline")
#     date_deadline = fields.Date()
#     state = fields.Selection([
#         ('draft', 'To Do'),
#         ('in_progress', 'In Progress'),
#         ('done', 'Done'),
#         ('cancel', 'Canceled'),
#     ], default='draft')
#     description = fields.Text()