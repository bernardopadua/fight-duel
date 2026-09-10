import Phaser from 'phaser';
interface ButtonConfig {
    width?: number;
    height?: number;
    textStyle?: Phaser.Types.GameObjects.Text.TextStyle;
    onClick?: () => void;
}
export class ImageButton extends Phaser.GameObjects.Container {
    private background: Phaser.GameObjects.Image;
    private label: Phaser.GameObjects.Text;
    private onClickCallback?: () => void;

    constructor(
        scene: Phaser.Scene,
        x: number,
        y: number,
        texture: string,
        text: string,
        config?: ButtonConfig
    ) {
        super(scene, x, y);

        this.background = scene.add.image(0, 0, texture);
        if (config?.width && config?.height) {
            this.background.setDisplaySize(config.width, config.height);
        }

        this.label = scene.add.text(0, 0, text, {
            fontSize: '16px',
            color: '#ffffff',
            align: 'center',
            ...config?.textStyle
        }).setOrigin(0.5);

        this.add([this.background, this.label]);

        const width = config?.width || this.background.width;
        const height = config?.height || this.background.height;
        this.setSize(width, height);
        this.setInteractive({ useHandCursor: true });

        this.on('pointerover', () => scene.tweens.add({ targets: this, scale: 1.05, duration: 100 }));
        this.on('pointerout', () => scene.tweens.add({ targets: this, scale: 1.0, duration: 100 }));
        this.on('pointerdown', () => scene.tweens.add({ targets: this, scale: 0.95, duration: 50 }));
        this.on('pointerup', () => {
            scene.tweens.add({ targets: this, scale: 1.0, duration: 50 });
            this.onClickCallback?.();
        });

        scene.add.existing(this);
    }

    public setText(newText: string) {
        this.label.setText(newText);
        return this;
    }

    public setDisabled(){
        this.label.setColor('#3d0000ff');
        this.background.setTexture('btn-world-select-disabled');
        return this;
    }

    public setEnabled(){
        this.label.setColor('#ffffff');
        this.background.setTexture('btn-world-select');
        return this;
    }

    public setOnClick(callback: () => void) {
        this.onClickCallback = callback;
        return this;
    }
}
