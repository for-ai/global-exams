Contains code for processing NEET question papers

Source : https://www.nta.ac.in/

**Files**
- Generator_Template.ipynb : Basic template for pipeline to process a NEET question paper 
- generator_codes : Contains examples of previous uses of the Generator_Template notebook for specific question papers



**For generating answer key JSON files**
Answer key maps can be easily extracted from Claude by passing either the pdf or an image of the answer key along with the following prompt: 
The following is an answer key for an exam. The pdf consists of question number followed by correct option (which is a number between 1 and 4). These are spread across 4 columns. Process the answer key and output it in a JSON file with question number as the key and correct answer as the value