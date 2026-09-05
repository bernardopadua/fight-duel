import { useRef, useEffect } from 'react';
import Phaser from 'phaser';

import { WorldScene } from './scenes/world-scene';

export function PhaserContainer() {
    const phaserContainer = useRef<HTMLDivElement | null>(null);
    const gameRef = useRef<Phaser.Game | null>(null);

    useEffect(() => {
        if (!phaserContainer.current || gameRef.current) return;
        const config: Phaser.Types.Core.GameConfig = {
            type: Phaser.AUTO,
            parent: phaserContainer.current,
            backgroundColor: '#0f172a',
            scale: {
                mode: Phaser.Scale.RESIZE, // Faz o canvas se ajustar à tela toda
                width: '100%',
                height: '100%',
            },
            scene: [WorldScene],
            physics: {
                default: 'arcade',
                arcade: { gravity: { x: 0, y: 0 }, debug: false },
            },
        };
        gameRef.current = new Phaser.Game(config);

        return () => {
            if (gameRef.current) {
                gameRef.current.destroy(true);
                gameRef.current = null;
            }
        };
    }, []);

    return (
        <div ref={phaserContainer} id="phaser-container" className="absolute inset-0 z-0" />
    );
}