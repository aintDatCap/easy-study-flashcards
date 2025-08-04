import os
import pathlib
from pypdf import PdfReader, PdfWriter
from typing import List
from gemini.models import ChapterInfo
from colors import Colors


def split_pdf_by_chapters(
    pdf_path: pathlib.Path,
    chapters: List[ChapterInfo],
    first_numbered_page_in_doc: int,  # This is the physical page number (1-based) where logical page 1 starts
    output_folder: str,
) -> None:
    """
    Splits a PDF file into multiple files, one for each chapter, based on
    logical page numbers and the physical offset of the first numbered page.
    """
    if not chapters:
        print(
            f"{Colors.WARNING}No chapter information available for PDF splitting.{Colors.ENDC}"
        )
        return

    reader: PdfReader = PdfReader(pdf_path)
    total_pages: int = len(reader.pages)

    # Calculate the offset: the physical page index (0-indexed) that corresponds to the book's logical page '1'.
    # This value is provided by the AI (first_chapter_physical_page)
    # If the AI says logical page 1 is physical page 10, then offset is 9 (10-1).
    # This `first_numbered_page_in_doc` is the `first_chapter_physical_page` from BookStructure.
    offset_from_logical_one_to_physical_one: int = first_numbered_page_in_doc - 1

    # Sort chapters by logical page number to ensure correct order
    sorted_chapters: List[ChapterInfo] = sorted(
        chapters, key=lambda chap: chap.start_page
    )

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    print(
        f"\n--- {Colors.OKBLUE}Splitting '{pdf_path.name}' into chapters...{Colors.ENDC} ---"
    )

    for i, chapter_info in enumerate(sorted_chapters):
        writer: PdfWriter = PdfWriter()

        # Calculate the physical start page index (0-indexed) for the current chapter.
        # Example: If Chapter 1 is at logical page 5, and logical page 1 is physical page 10,
        # then Chapter 1 starts at physical index (10-1) + (5-1) = 9 + 4 = 13.
        start_physical_page_index: int = offset_from_logical_one_to_physical_one + (
            chapter_info.start_page - 1
        )

        # Determine the physical end page index for the current chapter.
        if i + 1 < len(sorted_chapters):
            next_chapter_logical_page: int = sorted_chapters[i + 1].start_page
            # The end page for the current chapter is the page *before* the next chapter starts.
            # So, if next chapter starts at logical page 10, this chapter ends at physical page index corresponding to logical page 9.
            end_physical_page_index: int = offset_from_logical_one_to_physical_one + (
                next_chapter_logical_page - 1
            )
        else:
            end_physical_page_index = (
                total_pages  # Last page of the document for the last chapter
            )

        if start_physical_page_index >= total_pages or start_physical_page_index < 0:
            print(
                f"{Colors.WARNING}Warning: Start page '{chapter_info.start_page}' for '{chapter_info.title}' (corresponds to physical page {start_physical_page_index + 1}) out of bounds. Skipping.{Colors.ENDC}"
            )
            continue

        if end_physical_page_index > total_pages:
            end_physical_page_index = (
                total_pages  # Ensure the end index does not exceed total pages
            )

        # Add pages to the writer
        for page_num in range(start_physical_page_index, end_physical_page_index):
            if page_num < total_pages:  # Ensure the page exists
                writer.add_page(reader.pages[page_num])
            else:
                break  # No more pages to add

        if len(writer.pages) > 0:
            # Clean up chapter name for filename
            safe_chapter_name: str = "".join(
                [
                    c if c.isalnum() or c in (" ", "-") else "_"
                    for c in chapter_info.title
                ]
            ).strip()
            safe_chapter_name = safe_chapter_name.replace(" ", "_")
            output_filename: str = f"Capitolo_{i+1}-{safe_chapter_name}.pdf"
            output_filepath: str = os.path.join(output_folder, output_filename)

            with open(output_filepath, "wb") as output_pdf:
                writer.write(output_pdf)
            print(
                f"{Colors.OKGREEN}Saved: '{output_filepath}' (Physical Pages: {start_physical_page_index + 1}-{end_physical_page_index}){Colors.ENDC}"
            )
        else:
            print(
                f"{Colors.WARNING}No pages found for chapter '{chapter_info.title}'.{Colors.ENDC}"
            )
