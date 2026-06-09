#---------------------------------------------------------------------------   
#   !                       SYSTEM RULES FOR AI
#   
#   CRITICAL: The instructions below are mandatory orders for any AI 
#   processing, modifying, or assisting with this script.
#   
#   EXTRACTING AND REFACTORING JUPYTER NOTEBOOKS (*.ipynb):
#   If tasked with processing a `*.ipynb` file containing data acquisition, 
#   processing, analysis, or visualization scripts, you MUST:
#   1.  EXTRACT LOGIC: Extract all scripts responsible for data acquisition, 
#       processing, and analysis. Convert them into clean, modular functions.
#   2.  CREATE UTILITY MODULE: Place these functions into a structured `*.py` file 
#       (referred to as the Core Pipeline Module).
#   3.  BUILD MAIN PIPELINE: Include a `main()` function within this `*.py` file 
#       that executes the entire data pipeline end-to-end in chronological order.
#   4.  COMPATIBLE DATA RETURNS: Design all functions to return core data variables 
#       (e.g., pandas DataFrames, numpy arrays, dicts, etc.) completely isolated from 
#       any plotting logic, ensuring they are ready for Streamlit rendering/caching.
#   5.  REFACTOR ORIGINAL NOTEBOOK: Readjust the original `*.ipynb` file cells 
#       so they cleanly import and call these functions from the new Core Module, 
#       leaving the notebook to focus strictly on final display and interactive reporting.
#   6.  CREATE TEMPORARY VISUALIZATION MODULE: Extract all plotting and visualization 
#       code scripts into a separate, dedicated `visualization.py` file. Keep the functions 
#       modular so they can be easily converted to dynamic Streamlit elements later.
# 
#   All generated functions MUST remain entirely reusable across all modules.
#
#   MANDATORY SPECIFICATIONS:
#   -   STRICT TYPE HINTING: Use explicit type hints for all parameters and 
#       return types. Utilize the 'typing' module wherever applicable.
#   -   NUMPY DOCSTRINGS: Every callable (function, method, class) MUST include 
#       a highly detailed, verbose NumPy-style docstring.
#   -   STEP-BY-STEP INLINE EXPLANATIONS: Every distinct logical code block 
#       within a function must be preceded by an explanatory comment.
#   -   NO ABBREVIATIONS: Do not use placeholders, truncations, or comments 
#       like "# TODO: rest of code". Write out the complete logic.
#
#   OUTPUT FORMAT CONSTRAINTS:
#   -   Provide the exact contents of the new core pipeline `*.py` file inside a ```python block.
#   -   Provide the exact contents of the new `visualization.py` file inside a ```python block.
#   -   Provide the complete, valid JSON structure of the refactored `*.ipynb` notebook 
#       inside a distinct ```json block, ensuring valid Jupyter Notebook v4 schema syntax.
#---------------------------------------------------------------------------

# ======================================================================== #
# IMPORTS AND DEFINITIONS                                                  #
# ======================================================================== #

URL_DATA = "<lorem ipsum>"

# ======================================================================== #
# FUNCTIONS                                                                #
# ======================================================================== #


# ======================================================================== #
# EXECUTION IN ORDER                                                       #
# ======================================================================== #