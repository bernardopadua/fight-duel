import { useRef, useEffect, useMemo } from 'react';
import Phaser from 'phaser';

//SCENES
import { BootScene } from '@/game/scenes/boot-scene';
import { WorldScene } from '@/game/scenes/world-scene';
import { FightScene } from '@/game/scenes/fight-scene';

export function PhaserContainer() {
    const phaserContainer = useRef<HTMLDivElement | null>(null);
    const gameRef = useRef<Phaser.Game | null>(null);

    useEffect(() => {
        if (!phaserContainer.current || gameRef.current) return;
        const config: Phaser.Types.Core.GameConfig = {
            type: Phaser.AUTO,
            parent: phaserContainer.current,
            transparent: true,
            scale: {
                mode: Phaser.Scale.ENVELOP,
                width: 1280,
                height: 720,
                autoCenter: Phaser.Scale.CENTER_BOTH
            },
            scene: [BootScene, WorldScene, FightScene],
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
        <div ref={phaserContainer} 
            id="phaser-container" 
            className="absolute inset-0 z-0" 
            style={{backgroundImage: "url('https://science.nasa.gov/wp-content/uploads/2023/09/ssc2019-15b-med.jpg')", backgroundSize: "cover", backgroundPosition: "center", backgroundRepeat: "no-repeat"}}
        />
    );
}