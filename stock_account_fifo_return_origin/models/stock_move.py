# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        return_moves = self.filtered(
            lambda m: m._is_out() and m.origin_returned_move_id
        )
        other_moves = self - return_moves
        res = self.browse()
        if other_moves:
            res = super(StockMove, other_moves)._action_done(
                cancel_backorder=cancel_backorder
            )
        for move in return_moves:
            res |= super(
                StockMove,
                move.with_context(origin_returned_move=move.origin_returned_move_id),
            )._action_done(cancel_backorder=cancel_backorder)
        return res
