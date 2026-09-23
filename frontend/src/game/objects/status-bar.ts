export class StatusBar {
    private graphics: Phaser.GameObjects.Graphics;
    private width: number;
    private height: number;
    private offsetY: number;
    private color: number;
    private target: Phaser.GameObjects.Sprite;
    private scene: Phaser.Scene;

    private valueMax: number = 0;

    constructor(
        scene: Phaser.Scene, 
        target: Phaser.GameObjects.Sprite,
        offsetY: number,
        color: number,
        width = 60,
        height = 6
    ) {
        this.width = width;
        this.height = height;
        this.offsetY = offsetY;
        this.color = color;
        this.target = target;
        this.scene = scene;

        const onPostUpdate = () => {
            this.graphics.setPosition(
                this.target.x - this.width / 2, 
                this.target.y - this.target.height - this.offsetY
            );
        };

        this.graphics = this.scene.add.graphics().setDepth(3);
        this.scene.events.on('postupdate', onPostUpdate);
        this.scene.events.once('destroy', () => {
            this.scene.events.off('postupdate', onPostUpdate)
            this.graphics.destroy()
        });
    }
    public update(current: number, max: number | null) {
        this.graphics.clear();
        if (this.valueMax == 0) this.valueMax = max;
        const pct = Math.max(0, Math.min(1, current / this.valueMax));
        this.graphics.fillStyle(0x0f172a, 0.8);
        this.graphics.fillRoundedRect(0, 0, this.width, this.height, 3);
        if (pct > 0) {
            this.graphics.fillStyle(this.color, 1);
            this.graphics.fillRoundedRect(0, 0, this.width * pct, this.height, 3);
        }
    }
}