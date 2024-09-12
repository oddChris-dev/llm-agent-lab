import hashlib


class PageModel:
    def __init__(self, db, session_id, url, title=None, body=None, summary=None, parent_url_hash=None,
                 search_term=None, search_rank=None, last_loaded=None, last_opened=None, created_at=None):
        self.db = db
        self.url = url
        self.session_id = session_id
        self.title = title
        self.body = body
        self.summary = summary
        self.parent_url_hash = parent_url_hash
        self.search_term = search_term
        self.search_rank = search_rank
        self.last_loaded = last_loaded
        self.last_opened = last_opened
        self.created_at = created_at

    @classmethod
    def get_url_hash(cls, url):
        return hashlib.sha256(url.encode()).hexdigest()

    @classmethod
    def get_by_url(cls, db, url, session_id):
        url_hash = PageModel.get_url_hash(url)
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE url_hash = %s AND session_id = %s;")
        results = db.fetch_results(query, (url_hash, session_id))

        # If the page is found, return it
        if results:
            row = results[0]
            return cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])

        # If no page is found, create a new PageModel object
        if url:
            new_page = cls(
                db=db,
                session_id=session_id,
                url=url,
                title=None,  # Title is not loaded yet
                body=None,  # Body is not loaded yet
                summary=None,  # Summary is not generated yet
                parent_url_hash=None,  # No parent yet
                search_term=None,  # No search term related to this page yet
                search_rank=None,  # No search rank yet
                last_loaded=None,  # Page not yet loaded
                last_opened=None  # Page not yet opened
            )
            return new_page

        # Return None if the page is not found and no URL is provided to create a new one
        return None

    @classmethod
    def get_by_parent_url(cls, db, parent_url, session_id, max_results=10):
        parent_url_hash = PageModel.get_url_hash(parent_url)
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE parent_url_hash = %s AND session_id = %s "
                 "ORDER BY created_at DESC LIMIT %s;")
        results = db.fetch_results(query, (parent_url_hash, session_id, max_results))
        return [cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in results]


    @classmethod
    def get_by_not_parent_url(cls, db, parent_url, session_id, max_results=10):
        parent_url_hash = PageModel.get_url_hash(parent_url)
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE NOT is_summary_null AND (parent_url_hash IS NULL OR NOT parent_url_hash = %s) AND session_id = %s "
                 "ORDER BY created_at DESC LIMIT %s;")
        results = db.fetch_results(query, (parent_url_hash, session_id, max_results))
        return [cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in results]

    @classmethod
    def get_by_search_term(cls, db, search_term, session_id, max_results=10):
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE search_term = %s AND session_id = %s "
                 "ORDER BY created_at DESC LIMIT %s;")
        results = db.fetch_results(query, (search_term, session_id, max_results))
        return [cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in results]

    @classmethod
    def get_search_results(cls, db, session_id, max_results=10):
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE is_body_null AND search_term IS NOT NULL AND session_id = %s "
                 "ORDER BY created_at DESC LIMIT %s;")
        results = db.fetch_results(query, (session_id, max_results))
        return [cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in results]

    @classmethod
    def get_unsummarized_pages(cls, db, session_id, max_results=1):
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE is_summary_null AND session_id = %s ORDER BY created_at DESC LIMIT %s;")
        results = db.fetch_results(query, (session_id, max_results))
        return [cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in results]

    @classmethod
    def get_unloaded_pages(cls, db, session_id, max_results=100):
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE is_body_null AND session_id = %s ORDER BY created_at DESC LIMIT %s;")
        results = db.fetch_results(query, (session_id, max_results))
        return [cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in results]

    @classmethod
    def get_by_session_id(cls, db, session_id):
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE session_id = %s ORDER BY created_at DESC;")
        results = db.fetch_results(query, (session_id, ))
        return [cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in results]


    def save(self):
        if not self.url or not self.session_id:
            raise ValueError("url and session_id are required to save a page.")

        url_hash = PageModel.get_url_hash(self.url)

        query = ("""
            INSERT INTO pages (url_hash, session_id, url, title, body, summary, parent_url_hash, 
                               search_term, search_rank, last_loaded, last_opened)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            url = VALUES(url), title = VALUES(title), body = VALUES(body), summary = VALUES(summary), 
            parent_url_hash = VALUES(parent_url_hash), search_term = VALUES(search_term), 
            search_rank = VALUES(search_rank), last_loaded = VALUES(last_loaded), last_opened = VALUES(last_opened);
        """)
        self.db.execute_query(query, (url_hash, self.session_id, self.url, self.title, self.body, self.summary,
                                      self.parent_url_hash, self.search_term, self.search_rank,
                                      self.last_loaded, self.last_opened))

    def delete(self):
        if not self.url or not self.session_id:
            raise ValueError("url and session_id are required to delete a page.")
        url_hash = PageModel.get_url_hash(self.url)
        query = "DELETE FROM pages WHERE url_hash = %s AND session_id = %s;"
        self.db.execute_query(query, (url_hash, self.session_id))

    @classmethod
    def delete_by_session_id(cls, db, session_id):
        query = "DELETE FROM pages WHERE session_id = %s;"
        db.execute_query(query, (session_id, ))

    @classmethod
    def get_summarized(cls, db, session_id, page, per_page):
        """Retrieve paginated page entries."""
        offset = (page - 1) * per_page
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE NOT is_summary_null AND session_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s;")
        results = db.fetch_results(query, (session_id, per_page, offset))
        return [cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in results]

    @classmethod
    def get_paginated(cls, db, session_id, page, per_page):
        """Retrieve paginated page entries."""
        offset = (page - 1) * per_page
        query = ("SELECT session_id, url, title, body, summary, parent_url_hash, "
                 "search_term, search_rank, last_loaded, last_opened, created_at "
                 "FROM pages WHERE session_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s;")
        results = db.fetch_results(query, (session_id, per_page, offset))
        return [cls(db, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in results]

    @classmethod
    def get_total_count(cls, db, session_id):
        """Retrieve the total count of page entries for a session."""
        query = "SELECT COUNT(*) FROM pages WHERE session_id = %s;"
        result = db.fetch_results(query, (session_id,))
        return result[0][0]  # Return the count

    def set_parent_url(self, parent_url):
        self.parent_url_hash = PageModel.get_url_hash(parent_url)