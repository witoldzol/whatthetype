from a import foo 
from b import gives_c
import typemedaddy
from typemedaddy import convert_results_to_types,unify_types_in_final_result,update_code_with_types,reformat_code,update_files_with_new_signatures,update_files_with_new_imports, IMPORTS

with typemedaddy.trace() as data:
    c = gives_c()
    foo(c)
print("><"*100)
print(data)
print("===== STAGE 2 - ANALYSE TYPES IN DATA =====")
types_data = convert_results_to_types(data)
print("===== STAGE 5 - UNIFY ALL TYPES =====")
unified_types_data = unify_types_in_final_result(types_data)
print("===== STAGE 6 - UPDATE FILE WITH TYPES =====")
updated_function_signatures = update_code_with_types(types_data)
print("===== STAGE 7 - reformat updated code =====")
reformatted_function_signatures = reformat_code(updated_function_signatures)
print("===== STAGE 7 - reformat updated code =====")
# modules = update_files_with_new_signatures(reformatted_function_signatures, backup_file_suffix=None )
print("===== STAGE 8 - generate imports =====")
update_files_with_new_imports(IMPORTS)
