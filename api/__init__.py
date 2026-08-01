"""HTTP API layer for the InsurClaim AI React dashboard.

A thin Starlette wrapper around the existing Python pipeline. It does not
reimplement any investigation logic: it orchestrates the same calls the
Streamlit ``page_submit`` flow makes and streams progress to the browser.
"""
