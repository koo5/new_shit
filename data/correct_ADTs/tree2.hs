import Data.Tree

tree = Node "A" [Node "B" [], Node "C" [Node "D" [], Node "E" []]]

main = do
    print tree
    putStrLn $ drawTree tree
    putStrLn $ drawForest $ subForest tree

    print $ flatten tree
    print $ levels tree
    