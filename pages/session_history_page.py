from flask import request, render_template, redirect, url_for, Blueprint

from models.session_history_model import SessionHistoryModel
from pages.base_page import BasePage


class SessionHistoryPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('session_history_page', __name__, template_folder='pages/templates')
        self.routes()

    def routes(self):
        @self.blueprint.route('/session/<session_id>/history', methods=['POST', 'GET'])
        def session_history(session_id):
            # Get the current page number from the request, default to 1
            page = int(request.args.get('page', 1))
            per_page = 10  # Number of history entries per page

            session = self.get_session(session_id)
            total_count = SessionHistoryModel.get_total_count_by_session_id(self.app.db(), session_id)

            # Fetch paginated results
            history = SessionHistoryModel.get_paginated_by_session_id(self.app.db(), session_id, page, per_page)

            # Calculate total number of pages
            total_pages = (total_count + per_page - 1) // per_page

            # Number of navigation pages to show
            nav_pages = 5

            # Calculate the start and end pages for pagination
            if total_pages <= nav_pages:
                # If there are fewer total pages than nav_pages, show all pages
                start_page = 1
                end_page = total_pages
            else:
                # Make the current page centered within the page range
                start_page = max(1, page - (nav_pages // 2))
                end_page = min(total_pages, start_page + nav_pages - 1)

                # Adjust start_page and end_page if we are near the beginning or end
                if end_page - start_page < nav_pages - 1:
                    start_page = max(1, end_page - nav_pages + 1)

            # Calculate "Previous 5" and "Next 5" page links
            prev_page = max(1, page - nav_pages)
            next_page = min(total_pages, page + nav_pages)

            return render_template('session/session_history.html',
                                   session=session,
                                   history=history,
                                   done_form=self.DoneButtonForm(),
                                   delete_form=self.DeleteButtonForm(),
                                   page=page,
                                   total_pages=total_pages,
                                   start_page=start_page,
                                   end_page=end_page,
                                   prev_page=prev_page,
                                   next_page=next_page)

        @self.blueprint.route('/session/<session_id>/history/delete/<history_id>', methods=['POST'])
        def delete_history(session_id, history_id):
            history = self.get_session_history_by_id(history_id)

            if history:
                history.delete()

            return redirect(url_for('session_history_page.session_history', session_id=session_id))
