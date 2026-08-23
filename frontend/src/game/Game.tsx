function GameLayout(){
    return (
        <div className="grid grid-cols-2 grid-rows-[auto_1fr] h-screen">
            <aside className="border p-4">User info + Inventário</aside>
            <aside className="border p-4">Char selected</aside>
            <div id="phaser-container" className="col-span-2 bg-black" />
        </div>
    );
};

export default GameLayout;