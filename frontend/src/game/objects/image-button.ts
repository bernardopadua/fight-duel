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

    private buttonTexture: string;
    private buttonTextureDisabled: string;

    private isDisabled: boolean = false;

    private onClickCallback?: () => void;

    constructor(
        scene: Phaser.Scene,
        x: number,
        y: number,
        texture: string,
        textureDisabled: string,
        text: string,
        config?: ButtonConfig
    ) {
        super(scene, x, y);

        this.buttonTexture = texture;
        this.buttonTextureDisabled = textureDisabled;

        this.background = scene.add.image(0, 0, this.buttonTexture);
        if (config?.width && config?.height) {
            this.background.setDisplaySize(config.width, config.height);
        }

        if (text.length > 0){
            this.label = scene.add.text(0, 0, text, {
                fontSize: '16px',
                color: '#ffffff',
                align: 'center',
                ...config?.textStyle
            }).setOrigin(0.5);
            this.add([this.background, this.label]);
        } else {
            this.add([this.background]);
        }

        const width = config?.width || this.background.width;
        const height = config?.height || this.background.height;
        this.setSize(width, height);
        this.setInteractive({ useHandCursor: true });

        this.on('pointerover', () => { 
            if(this.isDisabled) return;
            scene.tweens.add({ targets: this, scale: 1.05, duration: 100 })
        });
        this.on('pointerout', () => scene.tweens.add({ targets: this, scale: 1.0, duration: 100 }));
        this.on('pointerdown', () => {
            if(this.isDisabled) return;
            scene.tweens.add({ targets: this, scale: 0.95, duration: 50 })
        });
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
        this.background.setTexture(this.buttonTextureDisabled);
        this.isDisabled = true;
        return this;
    }

    public setEnabled(){
        this.label.setColor('#ffffff');
        this.background.setTexture(this.buttonTexture);
        this.isDisabled = false;
        return this;
    }

    public setOnClick(callback: () => void) {
        this.onClickCallback = callback;
        return this;
    }
}
