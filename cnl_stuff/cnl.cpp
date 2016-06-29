//Controlled-english type theory, for user-friendly smart-contract
//development, compilable comments, informal proofs made formal, 
//code-by-voice, and more!

#include <iostream>
#include <fstream>

/*
Axiom:
<expression> is a <type-expression>

Definition:
<name> is _

*/

/*
Pi-types:

  "Pi A:B . C"

  logical usage:

  "for all A in B, C"

  function-types usage:


  "a function taking a _ and returning a <type-expression>"

*/

/*
functions/lambdas:

  "a function taking a _ and returning <expression>"

  this shows a need for using "a" in the english language
  for this application. if we didn't use "a" here, we would
  think to return the type itself, in which case this would
  be a function-definition for a type-constructor, rather than
  a a type-declaration for a regular function; consider:

  "a function taking an Int and returning an Int"
  this is a *type declaration* of function taking an
  Int and returning some Int.

 "a function taking an Int and returning Int" 
  this is a *function definition* of a type-constructor taking
  an Int and returning the set of all Ints.  
*/

/*
Sigma-types:

 "Sigma A:B . C:B->Type
 
 logical interpretation:
 "there exists A in B, such that C"

 dependent pair interpretation:
 "an object A in B along with C:B->Type"

*/

/*
Product types:

 "A*B"

 "A and B"

*/

/*
"The identity function is a function that takes a Level, n, and returns
a function that takes a Set n, t, and returns a function that takes a
t and returns a t."

"The identity function takes a Level, n, and returns a function that takes
a Set n, t, and returns a function that takes a t, x, and returns x."

*/

/*
Dependent record types:

 record Group {
   G : Set
   + : G -> G
   eid: sigma e : G . pi x : G . ( x + e = x)*(e + x = x)
   einv: pi x : G . sigma y : G . ( x + y = e)*(y + x = e)
   assoc: pi x, y , z : G . ((x + y) + z = x + (y + z)) 
 }

 record Group {
   G : Set
   + : sigma +:G->G . sigma e : G . pi x : G . ( x + e) ...
 }

 record Group {
  sigma G : Set . sigma + : G -> G . sigma eid : sigma e : G . pi x : G . ( x + e ....

 }

 sigma Group : Set . sigma G : Group. sigma + : G - > G . sigma eid ...

 "a group has a Set G, and a binary operation, +, on G, such that 
  there exists an object e in G such that for all .. "
 
 
*/

/*
Characters:
 Vowels:
 "aAeEiIoOuU"

 Consonants:
 "bBcCdDfFgGhHjJkKlLmMnNpPqQrRsStTvVwWxXyYzZ"


Digits:
 "0123456789"

Symbols:
 Reserved:
 ".,?;:()\"'"

 Reserved inside strings:
 "\"

 Non-reserved:
 "`~!@#%^&*_+={[}]|<>/"

 
White-space
 " "
 "
 "
*/

//typedef _ in_file_type
//classes are DRTs
//we can also make them into inductive types maybe



class cli_type{
	//options
	//file_type kb_file;
	//file_type query_file;
	cli_type(){

	}
}

class kb{

}

class query_type{

}

class result_type{

}


cli_type parse_cli(int argc, char *argv[]){
  return cli_type();
}

paragraphs_type split_to_paragraphs(... in){

}

sentences_type split_to_sentences(paragraph_type in){

}

mltt_expression parse_sentence(sentence_type in){
	
}

char* sprint_err_cantopenfile(char* file){
	return 'Couldn\'t open input file: ' ++ file;
}

kb_type parse_kb(char* file='', options_type options = options_type()){
  kb_type kb;

  ifstream ifs;
  ifs.open(file);
  if (!fin.good())
	return kb_type(false,sprint_err_cantopenfile(file));
  
  
  //parse into paragraphs
    //split by new-lines
  
  //parse paragraphs into sentences
   //split by periods  

  //parse sentences into MLTT

  //combine into kb

  return kb;
}

query_type parse_query(in_file_type in){

}

result_type query(query_type q){
  return 
}

//Needs side-effects to print output
int done(result_type res){ 
  return 0;
}

int main(int argc, char *argv[]){
  return done(run(parse_cli(argc,argv)));   		
}
