import Phaser from 'phaser';
export class WorldScene extends Phaser.Scene {
    private newText!: Phaser.GameObjects.Text;

    constructor() {
        super({ key: 'WorldScene' });
    }
    preload() {
    }
    create() {
        this.add.text(
            this.cameras.main.centerX,
            this.cameras.main.centerY,
            'Phaser 4 World Scene Running',
            { color: '#38bdf8', fontSize: '24px' }
        ).setOrigin(0.5);

        this.newText = this.add.text(
            this.cameras.main.centerX,
            this.cameras.main.centerY,
            'New Running',
            { color: '#38bdf8', fontSize: '32px' }
        ).setOrigin(0.8);
    }
    update() {
        this.newText.setText('Running: ' + this.game.loop.actualFps);
    }
}