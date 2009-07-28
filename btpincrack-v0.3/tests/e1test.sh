./btpincrack E1 0 0 0
echo "*************************"
echo "* Should be 05 6c 0f e6 *"
echo "*************************"
echo
./btpincrack E1 159dd9f43fc3d328efba0cd8a861fa57 bc3f30689647c8d7c5a03ca80a91eceb 7ca89b233c2d
echo "*************************"
echo "* Should be 8d 52 05 c5 *"
echo "*************************"
echo
./btpincrack E1 45298d06e46bac21421ddfbed94c032b 0891caee063f5da1809577ff94ccdcfb c62f19f6ce98
echo "*************************"
echo "* Should be 00 50 7e 5f *"
echo "*************************"
echo
./btpincrack E1 35949a914225fabad91995d226de1d92 0ecd61782b4128480c05dc45542b1b8c f428f0e624b3
echo "*************************"
echo "* Should be 80 e5 62 9c *"
echo "*************************"
echo
