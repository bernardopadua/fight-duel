import Phaser from 'phaser';

interface FightData {
    creatureName: string;
    creatureLevel: number;
}

export class FightScene extends Phaser.Scene {
    private creatureData! : FightData;
    
    constructor() {
        super({ key: "FightScene" });
    }
    init(data: FightData) {
        this.creatureData = data || {
            creatureName: "???",
            creatureLevel: 1
        };
    }
    preload() {
    }
    create() {
        const { width, height } = this.scale;

        this.add.text(
            width / 2, 80,
            "Fight Scene",
            { color: '#ef4444', fontSize: '28px', fontStyle: 'bold' },
        ).setOrigin(0.5);

        this.add.text(width / 2, 130, `${this.creatureData.creatureName} (Nv. ${this.creatureData.creatureLevel})`, {
            fontSize: '20px',
            color: '#f87171'
        }).setOrigin(0.5);

        this.add.text(width / 2, height - 100, '[ press space to flee ]', {
            fontSize: '16px',
            color: '#94a3b8'
        }).setOrigin(0.5);

        this.input.keyboard?.once('keydown-SPACE', ()=>{
            this.scene.start('WorldScene');
        });
    }
}