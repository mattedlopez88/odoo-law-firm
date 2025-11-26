# from odoo import models, fields
#
# # model that adds metadata, while the actual files live as ir.attachment
# # can also add later on an Evidence model for more strucuttured data
# class LawCaseDocument(models.Model):
#     _name = 'law.case.document'
#     _description = 'Case Document'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     name = fields.Char(required=True)
#     case_id = fields.Many2one('law.case', required=True)
#     document_type = fields.Selection([
#         ('pleading', 'Pleading'),
#         ('evidence', 'Evidence'),
#         ('contract', 'Contract'),
#         ('correspondence', 'Correspondence'),
#         ('internal', 'Internal Memo'),
#         ('other', 'Other'),
#     ], default='other')
#     attachment_id = fields.Many2one('ir.attachment', string="File", required=True)
#     date_uploaded = fields.Datetime(default=fields.Datetime.now)
#     uploaded_by_id = fields.Many2one('res.users', default=lambda self: self.env.user)
#     description = fields.Text()
#     is_confidential = fields.Boolean()