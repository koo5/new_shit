data Node a = Node {val :: a, left :: (Maybe (Node a)), right ::  (Maybe (Node a))}
data Tree a = Maybe (Node a)

data Tree2 a = Look a (Maybe (Tree2 a)) (Maybe (Tree2 a)) | Nothing


main = do
    let a = "initial"
    putStrLn a
    