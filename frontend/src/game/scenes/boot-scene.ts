import Phaser from 'phaser';

export class BootScene extends Phaser.Scene {
    constructor() {
        super({ key: 'BootScene' });
    }
    preload() {
        this.add.text(
            this.cameras.main.centerX,
            this.cameras.main.centerY,
            "Loading...",
            { color: '#ffffff', fontSize: '18px' },
        ).setOrigin(0.5);

        this.load.image('world-map', '/public/world/great-world.png');
        this.load.image('world-selector', '/public/ui/world-selection.png');
    }
    create() {
        this.scene.start('WorldScene');
    }
}