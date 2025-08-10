from pydantic import BaseModel, Field
from typing import List


class ChapterInfo(BaseModel):
    """Information about a single book chapter, including title and start page."""

    title: str = Field(description="The title of the chapter.")
    # start_page is now the logical page (as numbered in the book)
    start_page: int = Field(
        description="The 1-based page number (as numbered in the book) where the chapter starts."
    )


class ChaptersOnly(BaseModel):
    """Schema to extract only the list of chapters."""

    chapters: List[ChapterInfo] = Field(
        description="A list of main chapter information."
    )


class BookStructure(BaseModel):
    """Information about the book's structure, including chapters and the physical page of the first chapter."""

    chapters: List[ChapterInfo] = Field(
        description="A list of main chapter information."
    )
    first_chapter_physical_page: int = Field(
        description="The physical position in the PDF (1-based page) of the book's first numbered chapter."
    )
