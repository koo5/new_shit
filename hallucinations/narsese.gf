abstract Narsese = {
flags startcat = narsese;

cat
 LineComment;
 Task;
fun


    public Rule Input() {
        return sequence(
            zeroOrMore( //1 or more?
                    sequence(
                            firstOf(
                                    LineComment(),
                                    //PauseInput(),
                                    Task()
                            ),
                            s()
                    )
            ), eof() ) ;
    }


    public Rule Task() {

        Var<float[]> budget = new Var();
        Var<Character> punc = new Var();
        Var<Term> term = new Var();
        Var<Truth> truth = new Var();
        Var<Tense> tense = new Var(Tense.Eternal);

        return sequence(
                s(),

                optional( Budget(budget) ),


                Term(true, false),
                term.set((Term) pop()),

                SentencePunctuation(punc),

                optional(
                        s(), Tense(tense)
                ),

                optional(
                        s(), Truth(truth, tense)

                ),

                push(new Object[] { budget.get(), term.get(), punc.get(), truth.get(), tense.get() } )
                //push(getTask(budget, term, punc, truth, tense))

        );
    }





    Rule Term(boolean includeOperation, boolean includeMeta) {
        /*
                 <term> ::= <word>                             // an atomic constant term
                        | <variable>                         // an atomic variable term
                        | <compound-term>                    // a term with internal structure
                        | <statement>                        // a statement can serve as a term
        */




